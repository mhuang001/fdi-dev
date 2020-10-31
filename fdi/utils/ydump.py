# -*- coding: utf-8 -*-

import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap
import inspect
from collections import OrderedDict

from ruamel.yaml.compat import StringIO, ordereddict

import logging
# create logger
logger = logging.getLogger(__name__)


class MyYAML(YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


class MyRepresenter(RoundTripRepresenter):
    pass


ruamel.yaml.add_representer(OrderedDict, MyRepresenter.represent_dict,
                            representer=MyRepresenter)

yaml = MyYAML(typ='rt')
yaml.Representer = MyRepresenter
yaml.default_flow_style = False
yaml.width = 80
yaml.allow_unicode = True
yaml.compact(seq_seq=1, seq_map=True)

notinited = True


def yinit(mapping=6, sequence=4, offset=2, register=None):
    """ Initializes YAML.
    """
    global notinited

    yaml.indent(mapping=mapping, sequence=sequence, offset=offset)
    from ..dataset.classes import Classes

    for n, c in Classes.mapping.items():
        if inspect.isclass(c):
            yaml.register_class(c)

    if register:
        for c in register:
            if inspect.isclass(c):
                yaml.register_class(c)

    ruamel.yaml.add_representer(Classes.mapping['ODict'],
                                MyRepresenter.represent_dict,
                                representer=MyRepresenter)
    notinited = False
    return yaml


def ydump(od, stream=None, register=None, **kwds):
    """ YAML dump that outputs OrderedDict like dict.
    """

    global notinited
    if register is None:
        register = []
    if notinited:
        yinit(register=register)

    d = od

    if 0:
        return yaml.dump(d, default_flow_style=False, indent=4,
                         width=60, allow_unicode=True)
    else:
        return yaml.dump(d, stream, **kwds)

# https://stackoverflow.com/a/49048250


if 0:
    def represent_dictionary_order(self, dict_data):
        return self.represent_mapping('tag:yaml.org,2002:map', dict_data.items())

    def setup_yaml():
        yaml.add_representer(OrderedDict, represent_dictionary_order)

    setup_yaml()
