
from fdi.dataset.serializable import Serializable
import time
import os
import threading


class WelcomeModel(Serializable):
    def __getstate__(self):
        return {'foo': 'bar'}


def returnSomething(res='foo', msg='bar'):

    d = {
        'result': res,
        'msg': 4,  # msg,
        'time': time.time(),
        'pid': os.getpid(),
        'thread': threading.get_ident()
    }
    return d
