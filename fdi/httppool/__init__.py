def init_httppool_server(app):
    """ Init a global HTTP POOL """
    #global pc, Classes, PM, BASEURL, basepath, poolpath, pylookup

    # class namespace
    Classes = init_conf_clas(pc)
    lookup = ChainMap(Classes.mapping, globals(), vars(builtins))
    app.config['LOOKUP'] = lookup
    # users
    # effective group of current process
    uid, gid = getUidGid(pc['serveruser'])
    logger.info("Serveruser %s's uid %d and gid %d..." %
                (pc['serveruser'], uid, gid))
    # os.setuid(uid)
    # os.setgid(gid)
    xusers = {
        "rw": generate_password_hash(pc['node']['username']),
        "ro": generate_password_hash(pc['node']['password'])
    }
    users = [
        User(pc['node']['username'], pc['node']['password'], 'read_write'),
        User(pc['node']['ro_username'], pc['node']
             ['ro_password'], 'read_only')
    ]
    app.config['USERS'] = users

    # PoolManager is a singleton
    from ..pal.poolmanager import PoolManager as PM, DEFAULT_MEM_POOL
    if PM.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PM.getPool(DEFAULT_MEM_POOL).removeAll()
    logger.debug('Done cleanup PoolManager.')
    logger.debug('ProcID %d 1st reg %s' % (os.getpid(),
                                           str(app._got_first_request))
                 )
    PM.removeAll()
    app.config['POOLMANAGER'] = PM

    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'
    _basepath = PM.PlacePaths[scheme]
    poolpath = os.path.join(_basepath, pc['api_version'])

    if checkpath(poolpath, pc['serveruser']) is None:
        logger.error('Store path %s unavailable.' % poolpath)
        sys.exit(-2)

    app.config['POOLSCHEME'] = scheme
    app.config['POOLPATH'] = poolpath

######################################
#### Application Factory Function ####
######################################


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    config_object = config_object if config_object else getconfig.getConfig()
    app.config.from_object(config_object)
    logging.config.dictConfig(logdict.logdict)
    # '/var/log/pns-server.log'
    # logdict['handlers']['file']['filename'] = '/tmp/server.log'
    app.logger = logging.getLogger(__name__)
    # initialize_extensions(app)
    # register_blueprints(app)
    return app
