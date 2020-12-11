# -*- coding: utf-8 -*-
""" https://stackoverflow.com/a/43573798/13472124 """
from .common import lls, trbk

import sys
import os.path

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location


import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MyMetaFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        print('===', fullname, path, type(path))
        if path is None or path == "":
            path = [os.getcwd()]  # top level import --
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        print('***', name, path, type(path))
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue
            loader = MyLoader(filename)
            print('###', fullname, filename, submodule_locations, loader)
            ret = spec_from_file_location(fullname, filename,
                                          loader=loader,
                                          submodule_search_locations=submodule_locations)
            print('%%%', ret)
            return ret
        print('!!!', 'no loader', filename)
        return None  # we don't know how to import this


class SelectiveMetaFinder(MetaPathFinder):
    """ Raise ExcludedModule exception if loading modules whose names have any of cls.exclude.
    """
    class ExcludedModule(Exception):
        pass

    exclude = []

    def find_spec(self, fullname, path, target=None):
        # print('===', fullname, path, type(path))
        if path is None or path == "":
            path = [os.getcwd()]  # top level import --
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        #print('***', name, path, type(path), SelectiveMetaFinder.exclude)
        for x in SelectiveMetaFinder.exclude:
            if x == name:
                # print('!!!!!!!!!!!!!!!!!!!!!!!')
                raise(SelectiveMetaFinder.ExcludedModule(
                    name + ' is excluded from loading.'))
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue
            loader = MyLoader(filename)
            # print('###', fullname, filename, submodule_locations, loader)
            ret = spec_from_file_location(fullname, filename,
                                          loader=loader,
                                          submodule_search_locations=submodule_locations)
            #print('%%%', ret)
            return ret
        #print('!!!', 'no loader', filename)
        return None  # we don't know how to import this


class MyLoader(Loader):
    def __init__(self, filename):
        self.filename = filename
        #print('MMM ', filename)

    def create_module(self, spec):
        return None  # use default module creation semantics

    def exec_module(self, module):
        with open(self.filename, encoding='utf-8') as f:
            data = f.read()

        # manipulate data some way...
        #data += '\nb=42\n'
        logger.debug(self.filename)
        exec(data, vars(module))


def install():
    """Inserts the finder into the import machinery"""
    sys.meta_path.insert(0, MyMetaFinder())


def installSelectiveMetaFinder():
    """Inserts the finder into the import machinery"""
    sys.meta_path.insert(0, SelectiveMetaFinder())


def main(ipath='.'):
    if 0:
        install()

        import bar
        print(dir(bar))

    else:
        installSelectiveMetaFinder()
        SelectiveMetaFinder.exclude = ['notthis']
        # this is allowed
        from fdi.dataset.metadata import Parameter
        p = Parameter(0.99)
        assert p.value == 0.99
        # this is stopped.
        try:
            from fdi.dataset.notthis import BaseProduct
        except SelectiveMetaFinder.ExcludedModule as e:
            assert True
        else:
            assert False
        sys.path.insert(0, ipath)
        import bar
        assert hasattr(bar, 'k')


if __name__ == '__main__':

    main('tests')
    print('passed')
