import paho.mqtt.client as mqtt
import json
import logging
import queue
import threading
import time

CONN_RESULT = {}
CONN_RESULT[0] = "Connection accepted"
CONN_RESULT[1] = "Connection Refused, unacceptable protocol version"
CONN_RESULT[2] = "Connection Refused, identifier rejected"
CONN_RESULT[3] = "Connection Refused, Server unavailable"
CONN_RESULT[4] = "Connection Refused, bad user name or password"
CONN_RESULT[5] = "Connection Refused, not authorized"


class queuework2:

    keepalive = 60
    logger = None
    subclient = None

    def __init__(self, topics,
                 host=None, port=None, username=None, passwd=None,
                 client_id=None,
                 callback=None,
                 qos=1,
                 userdata=None,
                 clean_session=None,
                 ):
        self.init_logger()
        self.init_args(topics,
                       host=host, port=port, username=username, passwd=passwd,
                       on_msg_callback=callback,
                       client_id=client_id, qos=qos, userdata=userdata,
                       clean_session=clean_session)
        self.client = None
        pass

    def init_logger(self):
        logging.basicConfig(
            level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("queuework")
        pass

    def init_args(self, topics,
                  host=None, port=None, username=None, passwd=None,
                  client_id=None,
                  on_msg_callback=None,
                  qos=1, clean_session=None, userdata=None):
        self.topics = topics
        self._h = host
        self._p = port
        self.username = username
        self.passwd = passwd

        self.qos = qos
        self.client_id = client_id
        #
        self.msgq = queue.Queue()
        self.lock = threading.Lock()
        self.userdata = userdata
        self.on_msg_callback = on_msg_callback
        self.clean_session = clean_session
        self.reset = False
        # publish msg ids
        self.last_mid = -1
        self.mids_without_ack = []
        self.mwa_lock = threading.Lock()
        self.ordered_send = True

        pass

    def process_mid(self, mid, where):
        """ if mid is already in mwa, check it; if not put it in """

        mwa = self.mids_without_ack
        if mid and mid not in mwa:
            self.logger.debug(where + '%d not in MWA' % mid)
            self.last_mid = mid
            mwa.append(mid)
        else:
            if self.ordered_send:
                if mid > mwa[-1]:
                    self.logger.error(where + "Mid %d found before %d acknowledged." %
                                      (mid, mwa[-1]))
                elif mid < mwa[-1]:
                    self.logger.warning(where +
                                        "Mid %d acknowledged after %d has been sent." % (mid, mwa[-1]))
            mwa.remove(mid)
            self.logger.debug(where + 'MID %d removed from in MWA' % mid)
            msg = where + "Published with msg ID %d." % mid
            self.logger.debug(msg)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        if client.subscr_mid == mid:
            client.subscribed = True

    def on_connect(self, client, userdata, flags, rc):
        msg = CONN_RESULT[rc]

        has_prev_data = ' some' if flags['session present'] else ' no'
        logmsg = "Connected with result: " + msg + \
            has_prev_data + ' prev session data.'
        if rc:
            client.connected = False
            self.logger.warning(logmsg)
        else:
            client.connected = True
            self.logger.debug(logmsg)
        pass

    def on_disconnect(self, client, userdata, rc):
        client.connected = False
        if rc != 0:
            msg = CONN_RESULT[rc] + " Unexpected disconnection."
        else:
            msg = CONN_RESULT[rc]
        self.logger.debug("Disconnected with result: " + msg)
        pass

    def on_message(self, client, userdata, msg):
        self.lock.acquire()
        self.msgq.put(msg)
        self.logger.debug(msg)
        self.lock.release()
        pass

    def on_publish(self, client, userdata, mid):
        self.mwa_lock.acquire()
        self.process_mid(mid, 'on_publish: ')
        self.mwa_lock.release()

    def wait_for(self, client, msgType, period=0.1):
        """ Waiting for subscribe and publish to clear.

        http://www.steves-internet-guide.com/subscribing-topics-mqtt-client/
        return: 0 if successful.
        """
        if msgType == "SUBACK":
            if client.on_subscribe:
                limit = 0
                while not client.subscribed:
                    self.logger.debug("waiting suback")
                    client.loop(period)  # check for messages
                    # time.sleep(period)
                    limit += period
                    if limit > 10:
                        self.logger.warning(msgType + " timeout.")
                        return 1
            return 0

        elif msgType == "CONNACK":
            if client.on_connect:
                limit = 0
                while not client.connected:
                    self.logger.debug("waiting connack")
                    client.loop(period)  # check for messages
                    # time.sleep(period)
                    limit += period
                    if limit > 10:
                        self.logger.warning(msgType + " timeout.")
                        return 1
                    # print(':::::::::::::')
            return 0

        elif msgType == "PUBACK":
            if client.on_publish:
                limit = 0
                while len(self.mids_without_ack):
                    self.logger.debug("waiting puback %s",
                                      str(self.mids_without_ack))
                    client.loop(period)  # check for messages
                    # time.sleep(period)
                    limit += period
                    if limit > 10:
                        self.logger.warning(msgType + " timeout.")
                        return 1
            return 0
        else:
            self.logger.error('Bad msgType ' + msgType)
            return 2

    def init_client(self, force=False):

        if self.client and not force:
            return self.client
        self.client = None
        # self.logger.debug(type(self.userdata))
        username = self.username
        password = self.passwd
        host = self._h
        port = self._p
        qos = self.qos

        # init
        client = mqtt.Client(client_id=self.client_id,
                             clean_session=self.clean_session,
                             userdata=self.userdata)
        self.client = client
        client.max_inflight_messages_set(100)
        client.on_connect = self.on_connect
        client.on_message = self.on_msg_callback if \
            self.on_msg_callback else self.on_message
        client.on_publish = self.on_publish
        client.on_disconnect = self.on_disconnect
        client.username_pw_set(username, password)

        # connect
        client.connect(host, port, self.keepalive)
        client.connected = False
        self.logger.debug("Connect " + host + ":" + str(port))
        # subscription ms ids
        client.subscr_mid = -1
        if self.wait_for(client, 'CONNACK'):
            return None

        # topic subscription
        if isinstance(self.topics, list):
            if isinstance(self.topics[0], str):
                # topics is a list of topics
                topics = [(topic, qos) for topic in self.topics]
            else:
                topics = self.topics
        elif isinstance(self.topics, str):
            topics = self.topics
        else:
            self.logger.error('Bad format for subscrib() topics ' +
                              str(self.topics))
            return None
        rc, mid = client.subscribe(topics, qos=qos)
        client.subscr_mid = mid
        self.logger.debug("subscribe %s status: %s mid %s" %
                          (str(topics), CONN_RESULT[rc], str(mid)))
        client.subscribed = False
        if self.wait_for(client, 'SUBACK'):
            return None

        return client

    def start_send(self):

        return self.init_client()

    def send(self, topics, text, conn=True):

        if conn:
            self.client.connect(self._h, self._p, self.keepalive)
            # self.client.reconnect()
            self.client.connected = False
            self.logger.debug("Connect " + self._h + ":" + str(self._p))
            if self.wait_for(self.client, 'CONNACK'):
                return 1
        #
        rc, mid = self.client.publish(topics, payload=text, qos=self.qos)
        self.mwa_lock.acquire()
        self.process_mid(mid, 'send: ')
        self.mwa_lock.release()
        self.logger.debug("Publish status: %d mid %d" % (rc, mid))
        if conn:
            if self.wait_for(self.client, 'PUBACK'):
                return 1
        # client.loop_stop()
        # client.disconnect()

        return 0

    def stop_send(self):
        if self.client is not None:
            # self.client.disconnect()
            # self.client.loop_start()

            # self.client = None
            pass

    def start_receive(self, loop='no'):

        if self.init_client():
            #
            if loop == 'forever':
                self.client.loop_forever()
            elif loop == 'start':
                self.client.loop_start()
            else:
                pass
        #

    def stop_receive(self):
        if self.subclient is not None:
            self.subclient.loop_stop()
            self.subclient.disconnect()
            self.subclient = None
        pass

    def get_size():
        size = self.msgq.qsize()
        return size

    def get_message(self):
        try:
            self.lock.acquire()
            # m = self.msgq.get(True,self.timeout)
            m = self.msgq.get_nowait()
        except Exception:
            m = None
        finally:
            self.lock.release()

        return m
