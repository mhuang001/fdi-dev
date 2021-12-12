# -*- coding: utf-8 -*-

WebAPI = ['dereference', 'exists',
          'getCacheInfo', 'getCount', 'getDefinition', 'getHead', 'getId', 'getLastVersion', 'getPlace', 'getPoolname', 'getPoolurl', 'getPoolpath', 'getProductClasses', 'getReferenceCount', 'getScheme', 'getTagUrnMap', 'getTags', 'getUrn', 'getUrnId', 'getUrnObject', 'getVersions',
          'isAlive', 'isEmpty', 'loadDescriptors', 'loadProduct', 'lockpath',
          'meta', 'mfilter',
          'pfilter', 'poolname', 'poolurl', 'readHK', 'reference', 'remove', 'removeAll', 'removeTag', 'removeUrn', 'removekey',
          'saveDescriptors', 'saveProduct', 'saveProductRef', 'schematicLoad', 'schematicRemove', 'schematicSave', 'schematicSelect', 'schematicWipe', 'select', 'setTag', 'setup',
          'tagExists', 'writeHK']

publicRoute = '/csdb'
publicVersion = '/v1'
PublicServices = ['datatype', 'storage', 'pool', 'group', 'node', 'data', 'config']
PublicAPI = {
    'home': ['cache', 'err', 'package-time', 'time'],
    'datatype': ['']
}