# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class HkdataResult(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, classes: HkdataSpecific=None, urns: HkdataSpecific=None, tags: HkdataSpecific=None):  # noqa: E501
        """HkdataResult - a model defined in Swagger

        :param classes: The classes of this HkdataResult.  # noqa: E501
        :type classes: HkdataSpecific
        :param urns: The urns of this HkdataResult.  # noqa: E501
        :type urns: HkdataSpecific
        :param tags: The tags of this HkdataResult.  # noqa: E501
        :type tags: HkdataSpecific
        """
        self.swagger_types = {
            'classes': HkdataSpecific,
            'urns': HkdataSpecific,
            'tags': HkdataSpecific
        }

        self.attribute_map = {
            'classes': 'classes',
            'urns': 'urns',
            'tags': 'tags'
        }

        self._classes = classes
        self._urns = urns
        self._tags = tags

    @classmethod
    def from_dict(cls, dikt) -> 'HkdataResult':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The hkdata_result of this HkdataResult.  # noqa: E501
        :rtype: HkdataResult
        """
        return util.deserialize_model(dikt, cls)

    @property
    def classes(self) -> HkdataSpecific:
        """Gets the classes of this HkdataResult.


        :return: The classes of this HkdataResult.
        :rtype: HkdataSpecific
        """
        return self._classes

    @classes.setter
    def classes(self, classes: HkdataSpecific):
        """Sets the classes of this HkdataResult.


        :param classes: The classes of this HkdataResult.
        :type classes: HkdataSpecific
        """
        if classes is None:
            raise ValueError("Invalid value for `classes`, must not be `None`")  # noqa: E501

        self._classes = classes

    @property
    def urns(self) -> HkdataSpecific:
        """Gets the urns of this HkdataResult.


        :return: The urns of this HkdataResult.
        :rtype: HkdataSpecific
        """
        return self._urns

    @urns.setter
    def urns(self, urns: HkdataSpecific):
        """Sets the urns of this HkdataResult.


        :param urns: The urns of this HkdataResult.
        :type urns: HkdataSpecific
        """
        if urns is None:
            raise ValueError("Invalid value for `urns`, must not be `None`")  # noqa: E501

        self._urns = urns

    @property
    def tags(self) -> HkdataSpecific:
        """Gets the tags of this HkdataResult.


        :return: The tags of this HkdataResult.
        :rtype: HkdataSpecific
        """
        return self._tags

    @tags.setter
    def tags(self, tags: HkdataSpecific):
        """Sets the tags of this HkdataResult.


        :param tags: The tags of this HkdataResult.
        :type tags: HkdataSpecific
        """
        if tags is None:
            raise ValueError("Invalid value for `tags`, must not be `None`")  # noqa: E501

        self._tags = tags
