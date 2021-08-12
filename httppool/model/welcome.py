
from fdi.dataset.serializable import Serializable
import time


class WelcomeModel(Serializable):
    def __getstate__(self):
        return {'foo': 'bar'}


def returnSomething(res='foo', msg='bar'):

    d = {
        'result': res,
        'msg': 4,  # msg,
        'time': time.time()
    }
    return 2
