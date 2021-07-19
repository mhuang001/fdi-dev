

from fdi.utils.getconfig import getConfig
# default configuration is provided. Copy contents of svom/engisim/config.py to ~/.config/engisimlocal.py
pc = getConfig()

defaulturl = 'http://' + pc['node']['host'] + ':' + \
    str(pc['node']['port']) + pc['baseurl']


def urn2url(urn, contents='product'):
    """ Returns URL for accessing pools with a URN.

    contents:
    'product' for returning a product from the pool.
    'hk' for returning the housekeeping data of the pool.
    'classes' for returning the class housekeeping data of the pool.
    'urns' for returning the URN housekeeping data of the pool.
    'tags' for returning the tag housekeeping data of the pool.

    Example:
    IP=ip dir=/a/b/c files=/a/b//c/classes.jsn | urns.jsn | t.. | urn...

    with python:
    m.refs['myinput'] = special_ref
    ref=pstore.save(m)
    assert ref.urn == 'urn:http://ip:port/a/b/c/fdi.dataset.MapContext:203'
    p=ref.product
    myref=p.refs['myinput']

    with a pool:
    myref=pool.load('http://ip:port/v0.6/a/b/c/fdi.dataset.MapContext/203/refs/myinput')

    urn:http://ip:port/a/b/c/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/a/b/c/fdi.dataset.Product/203/meta/OBSID

    At the same time this is not allowed due to overlapping after 'c'

    urn:http://ip:port/a/b/d/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/a/b/c/d/

    This is also overlapping starting from '/'

    urn:http://ip:port/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/

    but for example this is allowed:

    urn:http://ip:port/a/k/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/a/k/


    """
    poolname, resourceclass, serialnumstr, scheme, \
        place, poolpath = parseUrn(urn)
    base = poolname + pc['baseurl']
    if contents == 'product':
        ret = base+'/'+resourceclass+'/'+serialnumstr
    elif contents == 'housekeeping':
        ret = base+'/hk'
    elif contents in ['classes', 'urns', 'tags']:
        ret = base+'/hk/' + contents
    else:
        raise(ValueError(contents))

    return ret
