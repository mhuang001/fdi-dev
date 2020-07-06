import abc
import json
from datetime import datetime
import logging
import requests
from requests.auth import HTTPBasicAuth
import fdi.dataset.serializable
from fdi.dataset.product import Product
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData
from fdi.dataset.finetime import FineTime1, utcobj
from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
from fdi.pal.context import Context, MapContext
from fdi.pal.productref import ProductRef
from fdi.pal.query import MetaQuery, StorageQuery
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.pal.productstorage import ProductStorage
from fdi.dataset.serializable import serializeClassID
from fdi.dataset.deserialize import deserializeClassID

class RequestFDI(abc.ABC):
    @abc.abstractmethod
    def request(self, url, **kwargs):
        pass

class GET(RequestFDI):
    def request(self, url, args):
        print(url)
        print(args)

class RequestFDIFactory:
    def create(self, method_name)-> RequestFDI:
        return eval(method_name)()
