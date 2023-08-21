__version_info__ = (1, 37, 0)
__version__ = '.'.join(map(str, __version_info__))
__revision__ = '1.36.1-4-g2e4ba48'

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
