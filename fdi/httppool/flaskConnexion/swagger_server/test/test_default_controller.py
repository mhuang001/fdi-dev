# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.generatebad import Generatebad  # noqa: E501
from swagger_server.models.generateok import Generateok  # noqa: E501
from swagger_server.models.hkdata import Hkdata  # noqa: E501
from swagger_server.models.hkdata_specific import HkdataSpecific  # noqa: E501
from swagger_server.models.product import Product  # noqa: E501
from swagger_server.models.productref import Productref  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_poolid_dataclass_sn_delete(self):
        """Test case for poolid_dataclass_sn_delete

        delete a data item from server
        """
        response = self.client.open(
            '/0.7/{poolid}/{dataclass}/{sn}'.format(poolid='poolid_example', dataclass='dataclass_example', sn=56),
            method='DELETE',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_poolid_dataclass_sn_get(self):
        """Test case for poolid_dataclass_sn_get

        Returns a data item in the pool.
        """
        response = self.client.open(
            '/0.7/{poolid}/{dataclass}/{sn}'.format(poolid='poolid_example', dataclass='dataclass_example', sn=56),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_poolid_dataclass_sn_post(self):
        """Test case for poolid_dataclass_sn_post

        upload a data item to server
        """
        response = self.client.open(
            '/0.7/{poolid}/{dataclass}/{sn}'.format(poolid='poolid_example', dataclass='dataclass_example', sn=56),
            method='POST',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_poolid_delete(self):
        """Test case for poolid_delete

        Removes all contents of the pool.
        """
        response = self.client.open(
            '/0.7/{poolid}'.format(poolid='poolid_example'),
            method='DELETE',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_poolid_hk_get(self):
        """Test case for poolid_hk_get

        All pool housekeeping data.
        """
        response = self.client.open(
            '/0.7/{poolid}/hk'.format(poolid='poolid_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_poolid_hk_metadata_get(self):
        """Test case for poolid_hk_metadata_get

        Returns a given type of pool housekeeping.
        """
        response = self.client.open(
            '/0.7/{poolid}/hk/{metadata}'.format(poolid='poolid_example', metadata='metadata_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
