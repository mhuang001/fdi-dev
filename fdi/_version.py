__version_info__ = (2, 4, 5)
__version__ = '.'.join(map(str, __version_info__))
__revision__ = '2.4.0.1-1-g07a0c44'

# fix include
# 2.4.4 pool notexist
# 2.4.3 upload visible
# 2.4.2 csdb prod upload return
# 2.4.1 fix ids that broke make test csdt
# 2.4.1 fix copy kw for array copying tofrom numpy
# 2.4.0.1 changing makefiles and dockerfile
# 2.4.0 to python10
# 2.3.2 misc fixes regarding NumericParameter
# 2.3.1 misc pool improvements. png upxdates
# 2.3.0 restore ReadOnlyDic
# 2.2.6 refactor attrstr, fits improvements for l1c
# 2.2.5 AId in fits. Fix missing params of deserialized parameters.
# 2.2.4 improve cache info report
# 2.2.3 make Lazy_Loading_ChainMap xxLook_Up output deepcopy be default.
# 2.2.1 minor improvement with real data
# 2.2.0 try ubuntu22.04 with dockerfile
# 2.1.3 merge develop to master
# 2.1.2 fix set_id fixture default.
# 2.1.1 fix making unawnted pools and missing version in poolurl
# 2.1.1 temporarily remove loker and all_doer prev in pools.py
# 2.1.0 fix missing user_id in session. fix login-logout and ctx
# 2.0.14 APIDocs route on swagger ui. fix missing 'current' in 'current_app'
# 2.0.13 de pdb
# 2.0.12 fix test bug.
# 2.0.11 get cloudd_token
# 2.0.10 paho mqtt back to == 1.6.1 in setup.py
# 2.0.9 fix fragile error hadling of fdi_requests
# 2.0.8 add toPng debug code
# 2.0.7 update tofits to image. paho reverted
# 2.0.6 shanghai
# 2.0.5 refactor iupload csdt prof defn code to main repo. get bin output ready in `toPng`
# 2.0.4 paho-mqtt upgrade to 2.1.0
# 2.0.3 namespace::load
# 2.0.2 de-svom in common::fullname
# 2.0.1 improve and validate quaternion; yaml2python add try: - except to imports; publicpool bug
# 2.0.0 Implement Quaternion with features, unified with Vector.
# 1.47.3 fix lru_cache bug in getConfig
# 1.47.2 make FineTime understand 'B' time format.
# 1.47.1 demo_* moved to fixture to not overwite outputs.py by test_schema
# 1.47.0 v2p for int and date non-MDs y2p 1.11. shorten prod full name.
# 1.46.11 common.py bug get_all_files
# 1.46.10 add 'verify' option to getToken. Act when getDataInfo gets error msg. get_all_in_dir matches every file.
# 1.46.9 fix watchdog-worker
# 1.46.8 correct change poistion in config.py
# 1.46.7 REAL add alias to config.py after commit in wrong window
# 1.46.5 fix paho.mqtt to v1.6.1
# 1.46.4 customize pools.yml and flasgger
# 1.46.3 for fxing csdb migration
# 1.46.2 same
# 1.46.1 update pools.yml
# 1.46.0 fix yaml2python mro-order sorting
# 1.45.2 no png2mp4
# 1.45.1 refactor quaternion.py
# 1.45.0 switch to pypng in toPNG after comparing python local, fpnge (no compression) and fpng-py (api not working)rr
# 1.44.3 fix wrong path and missing sleep entrypoint httppool_server_entrypoint_client.sh
# 1.44.2 missing
# 1.44.1 missing
# 1.44.0 add httppool_server_entrypoint_client.sh to enable docker-separated server testing
# 1.43.5 update .gitlab-ci. use background setting for fdi docker testhttp.
# 1.43.4 downgrade werkzeug to below 3.0.0 to avoid werkzeug.url import problem
# 1.43.3 change python3.8 to python3 to testsupport/fixtures.py
# 1.43.2 loadfile enhance csv reading
# 1.43.1 return L1B a L1keysOBS subclass.
# 1.43.0 add endian and numpyType to ArrayDataset
# 1.42.1 remake file name expansion and minor issues with tofits and FineTime.
# 1.42.0 overhaul pool server user and pool persistence. Reright FITS KW management with Namespace.
# 1.41.3 Fix mysterious indent bug in y2p and multiline comment in yml.
# 1.41.2 minor fixes to fits and metadata.
# 1.41.1 fix protocolError by using the writen png generator.
# 1.41.0 Since CreationDate is usually used for marking product production instead of event time, its type is changed to FineTime1.
# 1.40.7 add adapted tabulate wheel
# 1.40.6 minor fixed for the pipelines and wrong version id
# 1.40.5 improve FineTine an toFits to suppot L1B_vtse.
# 1.40.4 fix toFits return, docs, Flatten_compact separatoe set to ','.
# 1.40.3 wide meta extra. # fixed length fits
# 1.40.2 fix 2017 TAI. wip metaname separator
# 1.40.1 fix content-type bug.
# 1.40.0 star added to pool register api; introducing pool._user_urlbase
# 1.39.7 include traceback-with-variables
# 1.39.6 fix user_urlbase confusion and set loggerGPL.
# 1.39.5 new de-reffed pools yml, y2b glb bg fix;
# reinstate missing keep-alive header. experimenting namespace-based poolmanager.map; lock  implemented for pools.fix code 509. 
# 1.39.3 pool request keep-alive headerand other things.
# 1.39.2 Fix bug when secondary pool returns fits.
# 1.39.1 refactor fixture.py to move some contents to share fixture.
# 1.39.0 product of pure FITS io.
# 1.38.4 fix pools PM_S=PM_S, position of main(). gconfig.
# 1.38.3 fix fits output adaption; FineTime bug. missing _version.py update.rr
# 1.38.2 fdi_requests.get returns fits. FineTime rationalization.
# 1.38.1 add test option to ProductStorage.register(), fix test cases.
# 1.38.0 fix FineTime('0'); fix gettign token with missing host; fix publicclient pool wipe; add fits in out.
# 1.37.2 fix missing main() getconfig and yaml2python.
# 1.37.1 really fix dockerfile, for now.
# 1.37.0 attempt to add docker entrypoint inhrit.read_only pool avoid deleting.
# 1.36.1 fix getUrn bug. vtse working.
# 1.36.0 read_only pools, single PoolManager for all. remove pool info in session. improve pool request processing and debugging info.rr
# 1.35.6 fix typo. make running docker
# 1.35.5 fix pip cache spec passing in makefiles. fix typo .
# 1.35.4 reduce fixture.py dependence on config
# 1.35.3 history has one line for an error msg
# 1.35.2 add cmdline option to fixture.py
# 1.35.1 fix jsonschema to 4.17.3 to void depre warning and bugs but still have draft2019.,,
# 1.35.0 work out csdb uploading.
# 1.34.2 add history to tofits
# 1.34.1 fix typo and bug in yaml2python
# 1.34.0 Upload FITS product.
# 1.33.0 create fdi.testsupport.fixtures to make conftest reuseable. rewrite some fixtures.
# 1.32.5 dev env moving to ubuntu on win.
# 1.32.4 y2p changes pass test1,2. prod schema 1.9 with git hasf in FORMATV written
# 1.32.3 fix metadata wrong col order. center disply. refactor RefContainer str. n fits.
# 1.32.2login has no gui. add /pools/register GET api to httppool (v1.4). conftest.py refactored to start server properly in 3 ways, using parameterized fixtures. testhttp passes with mock server.
# 1.32.0 pass auth to aio_client, save csdb token in session cokies,
# 1.31.4 fix missing client arg in publicclient_pool.py
# 1.31.3 credential fixed for secondary poolurl regitration.
# 1.31.2 docker-making rationalized and deployed.
# 1.31.1 streamline docker making.
# 1.31.0 add revision log. add aiohttp_retry
# 1.30.4 fix for dockerbuilding
# 1.30.3 data included in wheel. test_schema not fixed when package installed.
# 1.30.2 common::find_all_files and makeSchemaStore accept imported packages.
# 1.30.1 testproducts gets version update for csdb debugging. csdb serialiswitched from json to fdi
# 1.30.0 GlobalPoolList not weakref anymore, working with server sessions. make login/out, saved cookies work. efficient update of pool HK by csdb backend. improve conftest efficiency for csdb.
# 1.29.0  Implement CSDB pool on HTTPpool v0.16, with secondary_url w/ fxed currentSN in csdb pool api /pool/delete.
# 1.28.3 arrange the order of parameters in yamt2python output.
# 1.28.2 tofits ans image.py adapted to latest pipeline_l1
# 1.28.1 fix 'set' bug and currentSN->0 bugs in pool; add set to serializable, csdb pool, tag and other working.
# 1.28.0 csdb overaul and asynhttp. bug fixes,
# 1.27.0 list input to `remove` localpool and subclasses. async io for HttpClientPool
# 1.26.2 Implement namespace-based getConfig(). Fix unregister bug in PS.remove()
# 1.26.1 simplify user config for httppool.
# 1.26.0 relate the 104 Connection Reset error to auto redirect to trailing '/' url. Add '/' to endpoints. add "/pools" to show pool info.
# 1.25.4 threaded test code. local httppool read/write prod 20-30ms
# 1.25.3 refactor query code
# 1.25.2 server remote debug
# 1.25.1 externalize docker tests.
# 1.25.0 getConfig and configuration improvement
# 1.24.4 requets timeout; logger_level_extras; single thread and python3.8 in wsgi; other improvement to get self-test pass for server docker.
# 1.24.3 improved config.py for docker, RW_USER, missing templates.
# 1.24.2 session works and all tests with live (fore/background) pools, w or w/o session. py3.9 in readthdoc.yml.'
# 1.24.1 intersphinx enabled for docs.
# 1.24.0 session for httppool, testing wih live mock server
# 1.23.1 greatly simplfies MetaData.toString with new Python-tabulate.
# 1.23.0 session and templates for httppool; extra fixed.
# 1.22.3 History docs and working on server
# 1.22.2 improve yaml2python parent sort; implement history tracing; Documents layout fix; Parameter takes anything as value unchecked.
