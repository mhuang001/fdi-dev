# -*- coding: utf-8 -*-

from .deserialize import deserialize
from ..utils.getconfig import get_mqtt_config
from .listener import EventListener, EventSender
from .serializable import serialize

import paho.mqtt.client as mqtt
from paho.mqtt.client import error_string, MQTT_ERR_NO_CONN

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
                 qos=1,
                 conn=True, subs=True,
                 **kwds):  # MqttRelayListener
        """ Starts a MQTT message queue and forward everything in the arguement list to the MQ serialized.

        host, port, username, passwd: if any is not provided, it is looked up in `config[...].
        """
        super().__init__(**kwds)

        if bool(host and port and username and passwd) is False:
            conf = get_mqtt_config()

        mq = mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            userdata=userdata if userdata else self)

        mq.username_pw_set(username if username else conf['mq_user'],
                           passwd if passwd else conf['mq_pass'])

        self.mq = mq
        self.topics = topics

        # for topic subscription
        if isinstance(self.topics, list):
            if isinstance(self.topics[0], str):
                # topics is a list of topics
                topics = [(topic, qos) for topic in self.topics]
            else:
                topics = self.topics
        elif isinstance(self.topics, str):
            topics = self.topics
        else:
            logger.error('Bad format for subscrib() topics ' +
                         str(self.topics))
            return None
        self.topics_for_subscription = topics

        self.host = host if host else conf['mq_host']
        self.port = port if port else int(conf['mq_port'])
        self.qos = qos

        self.keepalive = True
        self.username = username if username else conf['mq_user']
        self.passwd = passwd if passwd else conf['mq_pass']
        mq.username_pw_set(self.username, self.passwd)

        #mq.on_message = callback if callback else on_message
        mq.on_connect = on_connect

        self.mq.loop_start()
        # connect
        if conn:
            mq.connect(self.host, self.port, self.keepalive)
            logger.debug("Connect " + self.host + ":" + str(self.port))

    def targetChanged(self,  *args, **kwargs):
        """ Informs that an event has happened in a target of
        any type.
        """

        payload = list(chain(args, kwargs.items()))
        json_str = serialize(payload)

        logger.debug("send msg to [" + self.topics + "]")
        logger.debug(json_str)

        self.mq.reconnect()
        msg_info = self.mq.publish(
            self.topics, payload=json_str, qos=self.qos, retain=False)
        rc, mid = msg_info.rc, msg_info.mid

        if rc == MQTT_ERR_NO_CONN:
            raise Exception('why not connected?')
        logger.debug("Publish status: %d mid %d" % (rc, mid))
        logger.debug("send over")


class MqttRelaySender(EventSender):
    """ Gets MQTT messages and forwards to listeners.

    """

    def __init__(self, topics=None,
                 host=None, port=None, username=None, passwd=None,
                 callback=None, clean_session=None,
                 client_id=None, userdata=None, keepalive=60,
                 qos=1, **kwds):
        """ Starts a MQTT message queue and forward everything in the arguement list to the MQ serialized.

        host, port, username, passwd: if any is not provided, it is looked up in `config[...].
        """
        super().__init__(**kwds)

        if bool(host and port and username and passwd) is False:
            conf = get_mqtt_config()
        logger.debug('starting mq listening to '+str(topics))
        mq = mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            userdata=userdata if userdata else self)

        username = username if username else conf['mq_user']
        passwd = passwd if passwd else conf['mq_pass']
        mq.username_pw_set(username, passwd)
        host = host if host else conf['mq_host']
        port = port if port else int(conf['mq_port'])
        mq.on_message = on_message
        mq.connect(host, port, keepalive=keepalive)
        logger.debug("Connect " + host + ":" + str(port))
        rc, mid = mq.subscribe(topics, qos=qos)
        logger.debug("subscribe %s status: %s mid %s" %
                     (str(topics), error_string(rc), str(mid)))
        self.mq = mq

        mq.loop_start()


def on_connect(client, userdata, flags, rc):
    has_prev_data = ' some' if flags['session present'] else ' no'
    msg = mqtt.connack_string(rc)  # CONN_RESULT[rc]
    logmsg = "Connected with result: " + msg + \
        has_prev_data + ' prev session data.'

    rc, mid = userdata.mq.subscribe(userdata.topics_for_subscription,
                                    qos=userdata.qos)
    logger.debug("subscribe %s status: %s mid %s" %
                 (str(userdata.topics), error_string(rc), str(mid)))


def on_message(client, userdata, msg):
    mqtt_rel_s = userdata
    logger.debug("Received: " + msg.topic + ' ' + str(msg.payload))

    msgobj = deserialize(msg.payload.decode(encoding='utf-8'))

    mqtt_rel_s.fire(msgobj)
    mqtt_rel_s.last_msg = msgobj
