# -*- coding: utf-8 -*-

import yaml
from collections import OrderedDict

# https://stackoverflow.com/a/49048250


def represent_dictionary_order(self, dict_data):
    return self.represent_mapping('tag:yaml.org,2002:map', dict_data.items())


def setup_yaml():
    yaml.add_representer(OrderedDict, represent_dictionary_order)


setup_yaml()


def ydump(d):
    """ YAML dump that outputs OrderedDict like dict.
    """

    return yaml.dump(d, default_flow_style=False, indent=4,
                     width=60, allow_unicode=True)
