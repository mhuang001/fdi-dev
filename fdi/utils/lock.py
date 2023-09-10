

from .common import ( pathjoin,
                            )
from filelock import FileLock

import os
from os.path import join

Lock_Path_Base = '/tmp/fdi_locks_'  # getpass.getuser()

# @lru_cache(maxsize=256)
def makeLock(direc, op='w', base=Lock_Path_Base):
    """ returns the appropriate path based lock file object.

    creats the path if non-existing. Set lockpath-base permission to all-modify so other fdi users can use.

    Parameters
    ----------
    direc: str
       path name to append to `base` to form the path for `FileLock`.
    op: str
        'r' for readlock no-reading) 'w' for writelock (no-writing)
    base: str
        Default to `Lock_Path_Base`.
    """
    if not os.path.exists(base):
        os.makedirs(base, mode=0o777)

    lp = pathjoin(base, direc.replace('/', '_'))

    return FileLock(lp+'.r') if op == 'r' else FileLock(lp+'.w')

