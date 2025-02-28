#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
command line:
.. code-block:: bash
  
  python3 -c 'from svom.pipelines.pipemon import PM; PM(topics="proc..").report_status("start")'
  
  python3 -c 'from svom.pipelines.pipemon import PM; PM(topics="proc..", verbose=True).report_status("start")'

"""

from svom.schemas.jsonvalidator import get_schema, jsonValidator
from common.mq.queuework import queuework2, subscribe_multiple, install_callback_list

from fdi.utils.images import shortrainbowl, longrainbowl
from fdi.utils.getconfig import getConfig, get_mqtt_config


import paho.mqtt.client as pm_client
from paho.mqtt.client import error_string, Client, MQTT_ERR_NO_CONN, MQTT_ERR_NOT_SUPPORTED, MQTT_ERR_SUCCESS

import json
from jsonschema import validate, ValidationError, SchemaError
import copy
import time
import socket
import getpass
import os
import sys
import argparse
from functools import lru_cache
from collections import OrderedDict, defaultdict
import logging

# create logger
global logger


# @lru_cache(16)
def get_pipeline_envs(version='0.5'):
    """ Get pipeline environment variables and return them normalized in a mapping.
    """

    d = dict(((name, os.getenv(name, 'UNKNOWN'))
              for name in PIPELINE_ENV_VARS))
    if d['PIPELINE_CREATOR'] == 'UNKNOWN':
        d['PIPELINE_CREATOR'] = d['PIPELINE_UUID'] + \
            '_' + d['PIPELINE_NAME'] + \
            '_' + d['PIPELINE_NODE_NAME']
    for var in ('PIPELINE_TAGS',):
        if d[var] == 'UNKNOWN':
            d[var] = []
        else:
            d[var] = d[var].split('#')
    if d['PIPELINE_FORMATV'] == 'UNKNOWN':
        d['PIPELINE_FORMATV'] = version
    return d


class MQTT(queuework2):
    def __init__(self, *args, ignore=False, **kwds):
        """Initialize a specialized :class:`queuework.quework2`

        Parameters
        ----------
        ignore : bool
            ignore MQ errors.
        """

        self.ignore = ignore
        super().__init__(*args, **kwds)
        # self.client.max_queued_messages_set()

    def on_connect(self, client, userdata, flags, rc):
        if not client._topicqs:
            return
        super().on_connect(client, userdata, flags, rc)
        # subscribe
        subscribe_multiple(client, client._topicqs)

    def on_disconnect(self, client, userdata, rc):
        super().on_disconnect(client, userdata, rc)
        # flush outstanding msg
        if 0 and hasattr(userdata, 'mq'):
            client.reinitialise(client_id=userdata.mq.client_id,
                                clean_session=userdata.mq.clean_session,
                                userdata=userdata.mq.userdata)
        if hasattr(client, 'die'):
            logger.debug('exits.')
            # sys.exit(0)

    def on_message(self, client, userdata, msg):
        super().on_message(client, userdata, msg)
        body = bytes.decode(msg.payload)
        out = "#Received: " + msg.topic + " " + body
        self.logger.debug(out)


class CSDB_Monitor():
    def __init__(self,
                 info=None,
                 extra_args=None,
                 pmonlogger=None,
                 verbose=0,
                 **kwds):
        """ Setup monitoring of a pipeline.

        Parameters
        ----------
        info: `dict`
            pipeline information in key-value pairs. ::

            * name: pipeline name
            * contact: where to find the maintainer of this pipeline.
            * mq_args: MQ settings. Ref. `pipeline_l1.MQ_ARGS_DEFAULTS` docs.
            * version:
        pmonlogger: `logging.Logger`
            pipeline monitor logger. Defalut is None, a standard `logging.logger'
        verbose: bool
            If `pmonlogger` is not set, this sets logging level::

            * Defalut is 0, 1, 2 for level=30, 20, 10, respectively.
            * `True` for level=10, `False` 30.
        """

        global logger

        if pmonlogger is None:
            logging.basicConfig(stream=sys.stdout,
                                format='%(asctime)s.%(msecs)03d %(name)8s '
                                '%(process)d %(threadName)s %(levelname)3s '
                                '%(funcName)10s():%(lineno)3d- %(message)s',
                                datefmt="%Y-%m-%d %H:%M:%S")
            self.logger = logging.getLogger('CSDBMon')
            if issubclass(verbose.__class__, bool):
                verbose = 2 if verbose else 0

            if verbose >= 2:
                self.logger.setLevel(logging.DEBUG)
            elif verbose == 0:
                self.logger.setLevel(logging.WARNING)
            else:
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = pmonlogger
        logger = self.logger
        logger.debug('level %d' % (logger.getEffectiveLevel()))
        info = info if info else {}
        mq_args = info.pop('mq_args', None)
        self.info = info

        self.init_message_queue(mq_args)

        self.production_log = list()

        self.extra_init(extra_args)

    def init_message_queue(self, mq_args):
        """ use init/commandline options to override config options.

        if there is an 'mq' key in either config, the value is taken as the client object; otherwise instanciate one using the args.
        :mq_args: init/commandline options.

        """
        # topics is set from commandline usually
        mqttargs = get_mqtt_config()
        # commandline overrides config
        if mq_args is not None:
            mqttargs.update(mq_args)

        topics = mqttargs.pop('topics', '')

        if topics is None:
            self.topics = self.pub_topics = None
            self.mq = None
            self.logger.info('Receives None topic. No MQ.')
            return

        calling = mqttargs.pop('calling', False)
        self.ignore = mqttargs.get('ignore', False)
        self.qos = mqttargs.get('qos', 1)
        self.callbacks = mqttargs.get('callbacks', {})

        self.logger.debug('mqttargs= '+str(mqttargs))
        # add subscription topics here
        # start wuth existing ones if there are
        # sub_topics = mq0.topics if mq0 and hasattr(mq0, 'topics') else []
        sub_topics = []
        if topics:
            if issubclass(topics.__class__, list):
                sub_topics += topics
            else:
                sub_topics.append(topics)
        self.topics = sub_topics
        # no merge status monitoring topics into sub list
        # start with existing ones if there are
        self.logger.info('Will subscribe to MQTT topics %s.' % str(sub_topics))

        # pub_topics = mq0.pub_topics if mq0 and hasattr(mq0, 'pub_topics') else []
        pub_topics = []

        # accept exisiting MQTT object.
        if 'mq_from' in mqttargs and not calling:
            mq0 = mqttargs.pop('mq_from').pipemon.mq
            if mq0:
                # client = mq0.client
                # client.loop_stop()
                logger.debug('Use existing MQTT client')
                install_callback_list(mq0.client, topics,
                                      self.qos, self.callbacks)
                mq0.user_data2 = self
            self.mq = mq0
        else:
            args = copy.copy(mqttargs)
            args['host'] = args.pop('mq_host')
            args['port'] = args.pop('mq_port')
            args['username'] = args.pop('mq_user')
            args['passwd'] = args.pop('mq_pass')
            args['client_id'] = socket.gethostname()+'_' + getpass.getuser() + f'_{time.time()}'
            for tr in range(1, 4):
                try:
                    mq = MQTT(sub_topics, logger=self.logger, **args)
                    break
                except ConnectionRefusedError as e:
                    self.logger.warning('Connection problem %d / 3...' % tr)
            else:
                self.topics = self.pub_topics = None
                self.logger.error('MQ networks error. No MQ.')
                self.mq = None
                return
            self.logger.debug('Init new MQTT client ...')
            # subscribing is in on_connect
            mq.init_client(force=True, conn=False, subs=False)
            client = mq.client
            client.user_data_set(self)

            try:
                client.connect(mqttargs['mq_host'],
                               mqttargs['mq_port'], mq.keepalive)
            except OSError as e:
                self.logger.debug('host=%s port=%d Error %s' %
                                  (mqttargs['mq_host'], mqttargs['mq_port'], str(e)))
                if self.ignore:
                    self.topics = self.pub_topics = None
                    self.logger.error('NEtwork connection error. No MQ.')
                    self.mq = None
                    return
                else:
                    raise
            # wait for connection max 10 sec
            timeout = 10
            rc = 0
            while rc == 0 and timeout > 0:
                rc = client.loop(1.0)
                if client.is_connected():
                    break
                timeout -= 1
            else:
                self.topics = self.pub_topics = None
                self.logger.error('Cannot connect to MQ  %d %s. No MQ' %
                                  (rc, error_string(rc)))
                self.mq = None
                return

            print('MQTT client %s connected and listening to %s.' % (
                mq.client_id if client.is_connected() else 'not %s' % mq.client_id, str(sub_topics)))
            self.logger.debug('%s' % str(mqttargs))
            self.mq = mq

            # do not use this if using client.loop in while loop in pipelines.
            client.loop_start()
            self.logger.info("MQTT client %s started." % client._client_id)


    def extra_init(self, user_args):
        """ Override to initialize at the end of `Pipeline_L1.__init__().

        Parameters
        ----------
        user_args: dict
            the `extra_args` from `run()` and often commandline, as the second item returned by `Pipeline_l1.get_args`.
        """
        return

    
class CM(CSDB_Monitor):

    def __init__(self, *args, topics="", log=20, **kwds):
        """ Commandline helper class for CSDB_Monitor class.

        Parameter
        ---------
        topics : str
           the topic that overrides those in $environ
        log : str
           logging_level for mq
        """

        ma = kwds.pop('mq_args', {})
        ma['topics'] = topics
        ma['logging_level'] = log
        super().__init__(*args, mq_args=ma, **kwds)


if  __name__ == '__main__':

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "-u", "--upload", type=str,  nargs='+',
        default="-", help="The URN given here was sent back after uploading the product to the Pool/DB/storage. A 'upload' message in `proc/` topic and a 'new' message in `data/new/{datatype from urn}` topic will be sent. The same message is also printed on STDOUT accordingt o PIPE_MONITOR protocol.). The uploader is process the first word in the URN list if it does not start with 'urn/URN'.")
    parser.add_argument(
        "-r", "--topics", type=str, default="data/new/svom/products/#",
        help='Send to MQTT by the given topic. None for no messaging, "" for configured (start etc.)')
    parser.add_argument(
        "-N", "--no-JSON_validate", action='store_true', default=False,
        help="Do not validate message against JSON schema.")
    parser.add_argument(
        "-v", "--verbose", action='store_true', default=False,
        help="Print more details.")

    args, remainings = parser.parse_known_args()
    # xxxx
    CSDB_Monitor(mq_args={"topics": args.topics}, verbose=args.verbose)

    #from ..schemas.jsonvalidator import get_schema, jsonValidator
    #from common.mq.queuework import queuework2, subscribe_multiple, install_callback_list


    
    
