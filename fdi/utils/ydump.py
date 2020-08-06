# -*- coding: utf-8 -*-

from ..dataset.classes import Classes
import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap
import inspect
from collections import OrderedDict
import sys

from ruamel.yaml.compat import StringIO, ordereddict


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
yaml.indent(mapping=4, sequence=4, offset=2)
yaml.width = 80
yaml.allow_unicode = True
yaml.compact(seq_seq=1, seq_map=True)

for n, c in Classes.mapping.items():
    if inspect.isclass(c):
        yaml.register_class(c)

ruamel.yaml.add_representer(Classes.mapping['ODict'], MyRepresenter.represent_dict,
                            representer=MyRepresenter)


def ydump(od, stream=None):
    """ YAML dump that outputs OrderedDict like dict.
    """

    #d = ordereddict(od)
    # d.update(od)
    d = od
    if 0:
        return yaml.dump(d, default_flow_style=False, indent=4,
                         width=60, allow_unicode=True)
    else:
        return yaml.dump(d, stream)

# https://stackoverflow.com/a/49048250


if 0:
    def represent_dictionary_order(self, dict_data):
        return self.represent_mapping('tag:yaml.org,2002:map', dict_data.items())

    def setup_yaml():
        yaml.add_representer(OrderedDict, represent_dictionary_order)

    setup_yaml()
