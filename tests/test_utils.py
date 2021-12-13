# -*- coding: utf-8 -*-

from fdi.utils.fits_kw import FITS_KEYWORDS, getFitsKw
from fdi.utils.leapseconds import utc_to_tai, tai_to_utc, dTAI_UTC_from_utc, _fallback
from fdi.dataset.eq import deepcmp
from fdi.dataset.metadata import make_jsonable
from fdi.dataset.finetime import FineTime
from fdi.dataset.datatypes import Vector, Quaternion
from fdi.dataset.deserialize import Class_Look_Up, serialize_args, deserialize_args
from fdi.pal.urn import Urn
from fdi.pal.productref import ProductRef
from fdi.utils.checkjson import checkjson
from fdi.utils.loadfiles import loadcsv
from fdi.utils import moduleloader
from fdi.utils.common import fullname, wls
from fdi.utils.options import opt
from fdi.utils.fetch import fetch
from fdi.utils.loadfiles import loadMedia

import traceback
import copy
from datetime import timezone, timedelta, datetime
import sys
import os
import hashlib
import os.path
import pytest

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

if __name__ == '__main__' and __package__ == 'tests':
    # run by python -m tests.test_dataset
    pass
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/

    from pycontext import fdi

    from logdict import logdict
    import logging
    import logging.config

    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('%s logging level %d' %
                 (__name__, logger.getEffectiveLevel()))

    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)


def test_get_demo_product(demo_product):
    v, related = demo_product
    assert v['Browse'].data[1:4] == b'PNG'
    # print(v.yaml())
    p = v.getDefault()
    assert p == v['results']
    aref = ProductRef(related)
    v.refs['a'] = aref
    r0 = v.refs
    p['dset'] = 'foo'
    # refs is always the last
    assert list(v.keys())[-1] == 'refs'
    assert r0 == v.refs
    # existing key
    p['dset'] = 'foo'
    assert list(v.keys())[-1] == 'refs'
    assert r0 == v.refs
    checkjson(v, dbg=0)
    checkgeneral(v)


def checkgeneral(v):
    # can always add attributes
    t = 'random'
    v.testattr = t
    assert v.testattr == t
    try:
        m = v.notexists
    except AttributeError as e:
        assert str(e).split()[-1] == "'notexists'", traceback.print_exc()
    except:
        traceback.print_exc()
        assert false


def chk_sample_pd(p):
    v, s = fetch(["description"], p)
    assert v == p.description
    assert s == '.description'
    # metadatax
    with pytest.raises(KeyError):
        e = p.meta['extra']

    v, s = fetch(["meta", "speed"], p)
    assert v == p.meta['speed']
    assert s == '.meta["speed"]'
    # parameter
    v, s = fetch(["meta", "speed", "unit"], p)
    assert v == 'meter'
    assert v == p.meta['speed'].unit
    assert s == '.meta["speed"].unit'

    v, s = fetch(["meta", "speed", "value"], p)
    assert v == Vector((1.1, 2.2, 3.3))
    assert v == p.meta['speed'].value
    assert s == '.meta["speed"].value'
    v, s = fetch(["meta", "speed", "valid"], p)
    mkj = make_jsonable({(1, 22): 'normal', (30, 33): 'fast'})
    assert v == mkj
    assert v == make_jsonable(p.meta['speed'].valid)
    assert s == '.meta["speed"].valid'
    # TODO written is string
    # [[[1, 22], 'normal'], [[30, 33], 'fast']]
    v, s = fetch(["meta", "speed", "valid", 0, 1], p)
    assert v == 'normal'
    assert v == p.meta['speed'].valid[0][1]
    assert s == '.meta["speed"].valid[0][1]'
    #
    # validate execution
    v, s = fetch(["meta", "speed", "isValid", ], p)
    assert v == True
    assert v == p.meta['speed'].isValid()
    assert s == '.meta["speed"].isValid()'

    # datasets
    #
    v, s = fetch(["Environment Temperature", "unit"], p)
    assert v == 'C'
    assert v == p['Environment Temperature'].unit
    assert s == '["Environment Temperature"].unit'

    v, s = fetch(["Environment Temperature", "data"], p)
    assert v == [768, 767, 766, 4.4, 4.5, 4.6, 5.4E3]
    assert v == p['Environment Temperature'].data
    assert s == '["Environment Temperature"].data'

    # dataset has a parameter
    v, s = fetch(["Environment Temperature", "T0", "tai"], p)
    assert v == FineTime('2020-02-02T20:20:20.0202').tai

    # a 2D array dataset in compositedataset 'results'
    v, s = fetch(["results", 'calibration', "unit"], p)
    assert v == 'count'
    assert v == p['results']['calibration'].unit
    assert s == '["results"]["calibration"].unit'

    # data of a column in tabledataset within compositedataset
    v, s = fetch(["results", "Time_Energy_Pos", "Energy", "data"], p)
    t = [x * 1.0 for x in range(len(v))]
    assert v == [2 * x + 100 for x in t]
    assert v == p['results']['Time_Energy_Pos']['Energy'].data
    assert s == '["results"]["Time_Energy_Pos"]["Energy"].data'
    ys, s = fetch(["results", "Time_Energy_Pos", "y"], p)
    zs, s = fetch(["results", "Time_Energy_Pos", "z"], p)
    # y^2 + z^2 = 100 for all t
    assert all((y*y + z*z - 100) < 1e-5 for y, z in zip(ys.data, zs.data))


def test_fetch(demo_product):

    # simple nested structure
    v = {1: 2, 3: 4}
    u, s = fetch([3], v)
    assert u == 4
    assert s == '[3]'
    v = {'1': 2, 3: 4}
    u, s = fetch(['1'], v)
    assert u == 2
    assert s == '["1"]'
    v.update(d={'k': 99})
    u, s = fetch(['d', 'k'], v)
    assert u == 99
    assert s == '["d"]["k"]'
    # 3 levels
    v = [4, v,  5]
    w = copy.deepcopy(v)
    u, s = fetch([0], w)
    assert u == 4
    u, s = fetch([2], w)
    assert u == 5
    assert s == '[2]'
    u, s = fetch([1, 'd', 'k'], w)
    assert u == 99
    assert s == '[1]["d"]["k"]'

    # path is str
    assert fetch([2], w) == fetch('2', w)
    assert fetch([1, 'd', 'k'], w) == fetch(
        '1/d/k', w) == fetch('1.d.k', w, sep='.')
    assert fetch('/1/d/k ', w) == fetch('1.d.k', w, sep='.')
    assert fetch(' ', w, re='asd') == (w, 'asd')

    # objects

    class al(list):
        ala = 0
        @staticmethod
        def alb(): pass

        def alf(self, a, b=9):
            return a, b

        def __init__(self, *a, i=[8], **k):
            super().__init__(*a, **k)
            self.ald = i
        alc = {3: 4}
        ale = [99, 88]

    # init
    v = al(i=[1, 2])
    u, s = fetch(['ald'], v)
    assert u == [1, 2]
    assert s == '.ald'

    # class property list
    u, s = fetch(['ale', 1], v)
    assert u == 88
    assert s == '.ale[1]'

    # class property dict
    u, s = fetch(['alc', 3], v)
    assert u == 4
    assert s == '.alc[3]'

    # method
    u, s = fetch(['alb'], v)
    assert u is None
    assert s == '.alb()'

    # method w/ positional arg
    u, s = fetch(['alf__4.4'], v)
    assert u == (4.4, 9)
    assert s == '.alf(4.4)'

    # method w/ positional and keyword args
    allargs = serialize_args(4.4, [{"w": 77}, 65], not_quoted=True)
    assert allargs == '4.4__{"apiargs": [[{\"w\": 77}, 65]]}'
    u, s = fetch(['alf__' + allargs], v)
    assert u == (4.4, [{"w": 77}, 65])
    assert s == ".alf(4.4, [{'w': 77}, 65])"

    # method/function result
    u, s = fetch(['alf__' + allargs, 1, 0, 'w'], v)
    assert u == 77
    assert s == ".alf(4.4, [{'w': 77}, 65])[1][0][\"w\"]"

    class ad(dict):
        ada = 'p'
        adb = al([0, 6])

    v = ad(z=5, x=['b', 'n', {'m': 'j'}])
    v.ade = 'adee'

    u, s = fetch(['ada'], v)
    assert u == 'p'
    assert s == '.ada'

    u, s = fetch(['adb', 'ald', 0], v)
    assert u == 8
    assert s == '.adb.ald[0]'

    u, s = fetch(['x', 2, 'm'], v)
    assert u == 'j'
    assert s == '["x"][2]["m"]'

    # products
    p, r = demo_product
    chk_sample_pd(p)


def test_Fits_Kw():
    # Fits to Parameter name
    assert FITS_KEYWORDS['DATASUM'] == 'checksumData'
    assert FITS_KEYWORDS['DESC'] == 'description'
    assert FITS_KEYWORDS['CUNIT'] == 'cunit'
    assert getFitsKw('checksumData') == 'DATASUM'
    assert getFitsKw('description') == 'DESC'
    assert getFitsKw('cunit01') == 'CUNIT01'
    assert getFitsKw('description01234') == 'DESC34'
    # with pytest.raises(ValueError):
    assert getFitsKw('checksumData0123', 3) == 'DATAS123'
    assert getFitsKw('checksumData0123', 2) == 'DATASU23'
    with pytest.raises(TypeError):
        assert getFitsKw('foo0123', 5, (('foo', 'BAR'))) == 'BAR0123'
    assert getFitsKw('foo0123', 5, (('foo', 'BAR'),)) == 'BAR0123'


def test_loadcsv():
    csvf = '/tmp/fditest/testloadcsv.csv'
    a = 'as if ...'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    a = ' \t\n'+a
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    # blank line skipped
    a = a + '\n1 2. 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as', 1.0], '')
    assert v[1] == ('col2', ['if', 2.0], '')
    assert v[2] == ('col3', ['...', 3000.], '')

    # first line as header

    v = loadcsv(csvf, ' ', header=1)
    assert v[0] == ('as', [1.0], '')
    assert v[1] == ('if', [2.0], '')
    assert v[2] == ('...', [3000.], '')

    # a mixed line added. delimiter changed to ','
    a = 'as, if, ...\nm, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=1)
    assert v[0] == ('as', ['m', 1.0], '')
    assert v[1] == ('if', ['0.2', 2.0], '')
    assert v[2] == ('...', ['ev', 3000.], '')

    # anothrt line added. two header lines requested -- second line taken as unit line
    a = 'as, if, ...\n A, B, R \n m, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=2)
    assert v[0] == ('as', ['m', 1.0], 'A')
    assert v[1] == ('if', ['0.2', 2.0], 'B')
    assert v[2] == ('...', ['ev', 3000.], 'R')


def test_loadMedia():
    fname = 'bug.gif'
    fname = os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                      'resources'), fname)
    image = loadMedia(fname, 'image/gif')
    ho = hashlib.md5()
    ho.update(image.data)
    md5 = ho.hexdigest()
    assert md5 == '57bbbd6f8cdeafe6dc617f8969448e3b'


def test_moduleloader():

    moduleloader.main(ipath=os.path.abspath('tests'))


def test_fullname():
    assert fullname(Urn()) == 'fdi.pal.urn.Urn'
    assert fullname(Urn) == 'fdi.pal.urn.Urn'
    assert fullname('l') == 'str'


def test_wls():
    assert wls('') == ''
    assert wls('a') == 'a'
    assert wls('12', 2) == '12'
    assert wls('12345', 2) == '12\n34\n5'
    assert wls('12345678901234567') == '123456789012345\n67'
    # splitlines() removes trailing line-breaks
    assert wls('12345\n', 2) == '12\n34\n5'
    # no extr \n at width border
    assert wls('12\n345', 2) == '12\n34\n5'
    # no extr \n not at width border
    assert wls('1\n2345', 2) == '1\n23\n45'
    assert wls('1\n\n2345', 2) == '1\n23\n45'
    assert wls('12345\n\n', 2) == '12\n34\n5'
    assert wls('格式版本', 4) == '格式\n版本'
    assert wls('格式版本', 8) == '格式版本'
    assert wls('格式版本。', 10) == '格式版本。'
    assert wls('格\n式版本', 8) == '格\n式版本'
    assert wls('格式版本b', 4) == '格式\n版本\nb'
    assert wls('a格式版本', 4) == 'a格\n式版\n本'
    assert wls('格a式版本', 4) == '格a\n式版\n本'
    assert wls('格式a版本', 4) == '格式\na版\n本'
    assert wls('格式版a本', 4) == '格式\n版a\n本'
    assert wls('\ta', 1) == '#\na'
    assert wls('') == '#'
    # \r and \r\n etc are taken out as line-breaks.
    # ref https://docs.python.org/3.6/library/stdtypes.html#str.splitlines
    # the last \n is removed
    assert wls('\r') == ''
    # page separater is out, too
    assert wls(str(b'\x1c', 'utf-8')) == ''
    assert wls('格式\x01版a本', 4) == '格式\n#版a\n本'
    # fill
    assert wls('格\n式版本', 8, fill=' ') == '格      \n式版本  '
    assert wls('格式版本b', 4, fill=' ') == '格式\n版本\nb   '
    assert wls('格\th式版本b', 5, fill=' ') == '格#h \n式版 \n本b  '
    assert wls('产品标称的起始时间', 12, fill=' ') == '产品标称的起\n始时间      '


def test_opt(caplog):
    options = [
        {'long': 'helpme', 'char': 'h', 'default': False,
         'description': 'print help'},
        {'long': 'name=', 'char': 'n', 'default': 'Boo',
         'description': 'name of ship'},
        {'long': 'verbose', 'char': 'v', 'default': True,
         'description': 'print info'}
    ]
    # no args. defaults returned
    out = opt(options, [])
    assert out[0]['result'] == False
    assert out[1]['result'] == 'Boo'
    assert out[2]['result'] == True

    assert options[1]['long'] == 'name='

    # options given in short format
    out = opt(options, ['exe', '-h', '-n Awk', '-v'])
    assert out[0]['result'] == True
    # leading and trailing white spaces in args are removed
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # options given in long format
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == True
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # type of result is determined by that of the default
    options[0]['default'] = 0
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == 1

    # unplanned option and '--help' get exception and exits
    with pytest.raises(SystemExit):
        out = opt(options, ['exe', '--helpme', '--name=Awk', '-y'])
    assert 'option -y not recognized' in caplog.text

    with pytest.raises(SystemExit):
        h = copy.copy(options)
        h[0]['long'] = 'help'
        out = opt(h, ['exe', '--help', '--name=Awk', '-v'])


def check_conf(cfp, typ, getConfig):
    cfn = typ + 'local.py'
    cfp = os.path.expanduser(cfp)
    filec = os.path.join(cfp, cfn)
    os.system('rm -f ' + filec)
    conf = 'import os; %sconfig={"jk":98, "m":os.path.abspath(__file__)}' % typ
    with open(filec, 'w') as f:
        f.write(conf)
    # check conf file directory
    w = getConfig(conf=typ)
    assert w['jk'] == 98
    pfile = w['m']
    assert pfile.startswith(cfp)
    os.system('rm -f ' + filec)


def test_getConfig_init(getConfig):

    # no arg
    v = getConfig()
    from fdi.pns.config import pnsconfig
    # v is a superset
    assert all(n in v for n in pnsconfig)


def test_getConfig_noENV(getConfig):

    # non-default conf type
    typ = 'abc'
    # environment variable not set
    try:
        del os.environ['CONF_DIR']
    except:
        pass

    # default dir, there is  nothing
    # put mock in the default directory
    check_conf('~/.config', typ, getConfig)


def test_getConfig_conf(getConfig):

    # non-default conf type
    typ = 'abc'
    # specify directory
    cp = '/tmp'
    # environment variable
    os.environ['CONF_DIR_' + typ.upper()] = cp
    check_conf(cp, typ, getConfig)
    # non-existing. the file has been deleted by the check_conf in the last line
    w = getConfig(conf=typ)


def test_leapseconds():
    t0 = datetime(2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t0) == timedelta(seconds=37)
    # the above just means ...
    assert utc_to_tai(t0) - t0 == timedelta(seconds=37)
    t1 = datetime(1972, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t1) == timedelta(seconds=10)
    t2 = datetime(1970, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    # interpolation not implemented
    assert dTAI_UTC_from_utc(t2) == timedelta(seconds=4.213170)
    t3 = datetime(1968, 2, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t2) == timedelta(seconds=4.213170)
    t1958 = datetime(1958, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t1958) == timedelta(seconds=0)
    # leap seconds is added on transition
    t4 = datetime(2017, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert utc_to_tai(t4) - utc_to_tai(t4 - timedelta(seconds=1)) == \
        timedelta(seconds=2)
    print(_fallback.cache_info())
