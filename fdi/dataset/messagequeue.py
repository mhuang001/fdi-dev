# -*- coding: utf-8 -*-

from .serializable import Serializable
from .deserialize import deserialize
from .eq import DeepEqual
from ..utils.common import trbk
from ..utils.getconfig import getConfig
from .listener import EventListener, EventSender
from .serializable import serialize
from ..utils.queueworks import queuework2

from collections import namedtuple, OrderedDict
from itertools import chain
import logging

if 0:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)8s %(process)d %(threadName)s %(levelname)s %(funcName)10s() %(lineno)3d- %(message)s')

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MqttRelayListener(EventListener):
    """ Generic interface for sending anything heard to an MQTT message queue.
    """

    def __init__(self, topics=None,
                 host=None, port=None, username=None, passwd=None,
                 callback=None, clean_session=None,
                 client_id=None, userdata=None,
                 qos=1, **kwds):
        """ Starts a MQTT message queue and forward everything in the arguement list to the MQ serialized.

        host, port, username, passwd: if any is not provided, it is looked up in `config['mqtt'].
        """
        super().__init__(**kwds)

        if bool(host and port and username and passwd) is False:
            conf = getConfig(conf='pns')

        self.mq = queuework2(
            topics,
            host=host if host else conf['mqtt']['host'],
            port=port if port else conf['mqtt']['port'],
            username=username if username else conf['mqtt']['username'],
            passwd=passwd if passwd else conf['mqtt']['passwd'],
            client_id=client_id, callback=callback,
            userdata=userdata if userdata else self,
            clean_session=clean_session, qos=qos)
        self.mq.logger = logger

    def targetChanged(self,  *args, **kwargs):
        """ Informs that an event has happened in a target of
        any type.
        """

        payload = list(chain(args, kwargs.items()))
        json_str = serialize(payload)

        logger.debug("send msg to [" + self.mq.topics + "]")
        logger.debug(json_str)
        if self.mq.start_send():
            if self.mq.send(self.mq.topics, json_str, conn=False) == 0:
                logger.debug('Send successfully')
                self.mq.stop_send()
        logger.debug("send over")


class MqttRelaySender(EventSender):
    """ Gets MQTT messages and forwards to listeners.

    """

    def __init__(self, topics=None,
                 host=None, port=None, username=None, passwd=None,
                 callback=None, clean_session=None,
                 client_id=None, userdata=None,
                 qos=1, **kwds):
        """ Starts a MQTT message queue and forward everything in the arguement list to the MQ serialized.

        host, port, username, passwd: if any is not provided, it is looked up in `config['mqtt'].
        """
        super().__init__(**kwds)

        if bool(host and port and username and passwd) is False:
            conf = getConfig(conf='pns')
        logger.debug('starting mq listening to '+str(topics))
        self.mq = queuework2(
            topics,
            host=host if host else conf['mqtt']['host'],
            port=port if port else conf['mqtt']['port'],
            username=username if username else conf['mqtt']['username'],
            passwd=passwd if passwd else conf['mqtt']['passwd'],
            client_id=client_id, callback=on_message,
            userdata=userdata if userdata else self,
            clean_session=clean_session, qos=qos)
        self.mq.logger = logger
        self.mq.start_receive(loop='start')


def on_message(client, userdata, msg):
    mqtt_rel_s = userdata
    logger.debug("Received: " + msg.topic + ' ' + str(msg.payload))

    msgobj = deserialize(msg.payload.decode(encoding='utf-8'))

    mqtt_rel_s.fire(msgobj)
    mqtt_rel_s.last_msg = msgobj
    client.loop_start()
