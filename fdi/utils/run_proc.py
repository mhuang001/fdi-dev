# -*- coding: utf-8 -*-

from .common import lls, trbk
import pwd
from os import chown, chmod, environ, setuid, setgid
from subprocess import Popen, PIPE, TimeoutExpired, run as srun

import logging
# create logger
logger = logging.getLogger(__name__)


def run_proc(cmd, as_user, pwdir, timeout):
    """ Execute a shell command and return status.

    """

    try:
        # https://stackoverflow.com/a/6037494
        pw_record = pwd.getpwnam(as_user)
        user_name = pw_record.pw_name
        user_home_dir = pw_record.pw_dir
        user_uid = pw_record.pw_uid
        user_gid = pw_record.pw_gid
        env = environ.copy()
        env['HOME'] = user_home_dir
        env['LOGNAME'] = user_name
        env['PWD'] = pwdir
        env['USER'] = user_name

        def chusr(user_uid, user_gid):
            def result():
                setgid(user_gid)
                setuid(user_uid)
                logger.debug('set uid=%d gid=%d' % (user_uid, user_gid))
            return result

        executable = None

        # /etc/sudoer: apache ALL:(vvpp) NOPASSWD: ALL
        # gpasswd -a vvpp apache
        # cmd = ['sudo', '-u', as_user, 'bash', '-l', '-c'] + cmd
        # cmd = ['sudo', '-u', as_user] + cmd
        logger.debug('Popen %s env:%s uid: %d gid:%d' %
                     (str(cmd), lls(env, 40), user_uid, user_gid))
        proc = Popen(cmd, executable=executable,
                     stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     preexec_fn=None,
                     cwd=pwdir,
                     env=env, shell=False,
                     encoding='utf-8')  # , universal_newlines=True)
    except Exception as e:
        msg = trbk(e)
        return {'returncode': -1, 'message': msg}

    sta = {'command': str(cmd)}

    try:
        sta['stdout'], sta['stderr'] = proc.communicate(timeout=timeout)
        sta['returncode'] = proc.returncode
    except TimeoutExpired:
        # The child process is not killed if the timeout expista,
        # so in order to cleanup properly a well-behaved application
        # should kill the child process and finish communication
        # https://docs.python.org/3.6/library/subprocess.html?highlight=subprocess#subprocess.Popen.communicate
        proc.kill()
        sta['stdout'], sta['stderr'] = proc.communicate()
        sta['returncode'] = proc.returncode

    return sta
