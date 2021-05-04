# -*- coding: utf-8 -*-


from fdi.utils import getconfig

import pytest


@pytest.fixture(scope="package")
def pc():
    """ get configuration.

    """
    pc = getconfig.getConfig()
    return pc
