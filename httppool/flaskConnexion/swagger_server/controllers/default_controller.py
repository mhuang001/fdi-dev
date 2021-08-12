import connexion
import six

from swagger_server.models.generatebad import Generatebad  # noqa: E501
from swagger_server.models.generateok import Generateok  # noqa: E501
from swagger_server.models.hkdata import Hkdata  # noqa: E501
from swagger_server.models.hkdata_specific import HkdataSpecific  # noqa: E501
from swagger_server.models.product import Product  # noqa: E501
from swagger_server.models.productref import Productref  # noqa: E501
from swagger_server import util


def poolid_dataclass_sn_delete(poolid, dataclass, sn):  # noqa: E501
    """delete a data item from server

    delete specific data item from server by passing poolID, type and index # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str
    :param dataclass: type of data
    :type dataclass: str
    :param sn: index, within the given data type, of the data to retreive
    :type sn: int

    :rtype: None
    """
    return 'do some magic!'


def poolid_dataclass_sn_get(poolid, dataclass, sn):  # noqa: E501
    """Returns a data item in the pool.

    requests a data item in the pool by passing poolID, dataclass and its index. # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str
    :param dataclass: type of data
    :type dataclass: str
    :param sn: index, within the given data type, of the data to retreive
    :type sn: int

    :rtype: Product
    """
    return 'do some magic!'


def poolid_dataclass_sn_post(poolid, dataclass, sn):  # noqa: E501
    """upload a data item to server

    upload a data item to server # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str
    :param dataclass: type of data
    :type dataclass: str
    :param sn: index, within the given data type, of the data to retreive
    :type sn: int

    :rtype: Productref
    """
    return 'do some magic!'


def poolid_delete(poolid):  # noqa: E501
    """Removes all contents of the pool.

    requests all data in the pool be removed by passing poolID. # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str

    :rtype: Generateok
    """
    return 'do some magic!'


def poolid_hk_get(poolid):  # noqa: E501
    """All pool housekeeping data.

    With poolID return all pool housekeeping data. # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str

    :rtype: Hkdata
    """
    return 'do some magic!'


def poolid_hk_metadata_get(poolid, metadata):  # noqa: E501
    """Returns a given type of pool housekeeping.

    requests pool housekeeping data of the specified type: classes or urns or tags ... # noqa: E501

    :param poolid: poolID (also called pool name)
    :type poolid: str
    :param metadata: one of classes, urns, tags ...
    :type metadata: str

    :rtype: HkdataSpecific
    """
    return 'do some magic!'
