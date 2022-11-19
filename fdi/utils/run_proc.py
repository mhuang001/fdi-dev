# -*- coding: utf-8 -*-

from .common import lls, trbk
import pwd
import os
import signal
from subprocess import (Popen,
                        PIPE,
                        TimeoutExpired,
                        )

import logging
# create logger
logger = logging.getLogger(__name__)


def run_proc(cmd, as_user, pwdir, timeout, pty=PIPE):
    """Execute a shell command and return status.

    Parameters
    ----------
    cmd : list
        A list of command line strings. e.g. from ``shelex.split("ls -t")``
    as_user : str
        execute as user. overrides env var `USER` and
        `pwd.getpwnam()`.
    pwdir : str
        overides what is in `pwd.getpwnam()`.
    timeout : float
        sets `popen` timeout. If triggers will get the processed
        killed.
    pty : int
        passed to `stdin`, `stdout`, `stderr` in `popen`.
    pid_file: str2
        Name of the file that has the `cmd` process ID. Needed to kill by grand parents.

    Returns
    -------
    dict
        If  `try` block fails when starting, a dictionary of:

    :returncode: the process return code. -9 if killed aftet timeout.
    :message: Error message from exception.

         If starting successfully, a dictionary of:

    :command: The `cmd` from input.
    :returncode: the process `returncode`. `-9` if killed aftet timeout.
    :stdout:, stderr: from `communicate()` of the process.
    :message: Announce success and why may have been killed.
    """

    try:
        # https://stackoverflow.com/a/6037494

        user_name = as_user if as_user else os.environ.get('USER')
        pw_record = pwd.getpwnam(user_name)
        user_name = pw_record.pw_name
        user_home_dir = pw_record.pw_dir
        user_uid = pw_record.pw_uid
        user_gid = pw_record.pw_gid
        env = os.environ.copy()
        env['HOME'] = user_home_dir
        env['LOGNAME'] = env['USER'] = user_name
        env['PWD'] = pwdir
        env['SystemRoot'] = ''

        executable = None

        def chusr(user_uid, user_gid):
            def sid():
                setgid(user_gid)
                setuid(user_uid)
                logger.debug('set uid=%d gid=%d' % (user_uid, user_gid))
            return sid

        # /etc/sudoer: fdi ALL:(vvpp) NOPASSWD: ALL
        # gpasswd -a xxxx fdi
        # cmd = ['sudo', '-u', as_user, 'bash', '-l', '-c'] + cmd
        # cmd = ['sudo', '-u', as_user] + cmd

        shell = False
        logger.debug('Popen %s env:%s uid: %d gid:%d' %
                     (str(cmd), lls(env, 40), user_uid, user_gid))
        proc = Popen(cmd, executable=executable,
                     stdin=pty, stdout=pty, stderr=pty,
                     preexec_fn=None,
                     cwd=pwdir,
                     env=env, shell=shell,
                     start_new_session=False,
                     encoding='utf-8')  # , universal_newlines=True)
    except Exception as e:
        msg = trbk(e)
        logger.info('Running popen got exception. '+msg)
        return {'returncode': -1, 'message': msg}

    sta = {'command': str(cmd)}
    try:
        sta['stdout'], sta['stderr'] = proc.communicate(timeout=timeout)
        sta['returncode'] = proc.returncode
        msg = 'Successful.'
    except TimeoutExpired:
        # The child process is not killed if the timeout expires,
        # so in order to cleanup properly a well-behaved application
        # should kill the child process and finish communication
        # https://docs.python.org/3.6/library/subprocess.html?highlight=subprocess#subprocess.Popen.communicate
        proc.kill()
        # kill subprocess, too
        # os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        sta['stdout'], sta['stderr'] = proc.communicate()
        sta['returncode'] = proc.returncode
        msg = 'PID %d is terminated after pre-set timed-out %d sec.' % (
            proc.pid, timeout)
    sta['message'] = msg
    return sta


def kill_processes(pid):
    """Kills parent and children processess

    https://codeigo.com/python/kill-subprocess
    """
    import psutil
    parent = psutil.Process(pid)
    # kill all the child processes
    for child in parent.children(recursive=True):
        print(child)
        child.kill()
    # kill the parent process
    print(parent)
    parent.kill()
