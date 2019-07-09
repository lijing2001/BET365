import sys
#from pprint import pprint

import ssl
import urllib.request,http.cookiejar

from autobahn.twisted.websocket import connectWS, WebSocketClientFactory, WebSocketClientProtocol
from autobahn.websocket.compress import (
    PerMessageDeflateOffer,
    PerMessageDeflateResponse,
    PerMessageDeflateResponseAccept,
)
from requests import request
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
#from twisted.python import log
from txaio import start_logging, use_twisted

#sys.setrecursionlimit(9000000) #这里设置大一些
use_twisted()

#start_logging(level='none')


class DiffusionClient(object):

    _USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/5.0 (KHTML, like Gecko) Chrome/5.0 Safari/5.0'

    def __init__(self, connection_url, trigger, session_url=None, protocol=None, headers={}, topics=[]):
        self._message_handler = self
        self._connection_url = connection_url
        self._trigger = trigger
        self._session_url = session_url
        self._protocol = protocol
        self._headers = headers
        self._topics = topics

        self._session_id = self._get_session_id()

        self._factory = self._get_factory()

        self._connection = None

    def _get_factory(self):
        factory = DiffusionFactory(
            self._connection_url,
            headers=self._headers,
            protocols=self._get_protocols(),
            useragent=self._USER_AGENT,
        )

        factory.message_handler = self._message_handler
        factory.trigger = self._trigger
        factory.session_id = self._session_id
        factory.protocol = DiffusionProtocol
        factory.topics = self._topics

        factory.setProtocolOptions(perMessageCompressionAccept=self._accept)
        factory.setProtocolOptions(perMessageCompressionOffers=[self._get_offer()])

        return factory

    def _get_protocols(self):
        if self._protocol:
            return [self._protocol]
        return []

    def _accept(self, response):
        if isinstance(response, PerMessageDeflateResponse):
            return PerMessageDeflateResponseAccept(response)

    def _get_offer(self):
        return PerMessageDeflateOffer(
            accept_max_window_bits=True,
            accept_no_context_takeover=False,
            request_max_window_bits=0,
            request_no_context_takeover=False,
        )

    def _get_session_id(self):
        if not self._session_url:
            return None
        print('fetching session id...')
        cookie = None
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            cookie = http.cookiejar.CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener(handler)
            response = opener.open(self._session_url)
            #response = request(method='GET', url=self._session_url,verify=False)
        except Exception as err:
            print ('Exception: ', err)
            pass
        if not response:
            print('session id: N/A')
            return
        for item in cookie:
            #print(item.name+"="+item.value)
            if item.name == "pstk":
                session_id = item.value
        print('session id: ' ,session_id)
        return session_id

    def can_connect(self):
        return self._session_url is None or self._session_id is not None

    def connect(self):
        self._message_handler.pre_connect()
        #log.msg('opening connection...')
        print('opening connection...')
        # Reference: http://twistedmatrix.com/documents/current/core/howto/threading.html#invoking-twisted-from-other-threads # noqa
        # reactor.callFromThread(connectWS, self._factory)

    def disconnect(self):
        print('closing connection...')
        self._connection.disconnect()

    def pre_connect(self):
        print('connecting...')

    def post_connect(self):
        print('connected')

    def pre_message(self):
        print('receiving message...')

    def post_message(self, diffusion_message):
        print('received message: ',diffusion_message)


class DiffusionFactory(WebSocketClientFactory, ReconnectingClientFactory):
    """
    maxDelay = 3600 (seconds)
    initialDelay = 1.0 (seconds)
    factor = 2.7182818284590451 # (math.e)
    jitter = 0.11962656472
    Reference: https://github.com/twisted/twisted/blob/trunk/src/twisted/internet/protocol.py#L332
    """

    def clientConnectionFailed(self, connector, reason):
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        self.retry(connector)


class DiffusionMessage(object):

    def __init__(self, type, topic, body, headers):
        self.type = type
        self.topic = topic
        self.body = body
        self.headers = headers

    def __repr__(self):
        return '%s(%r, %r, %r, %r)' % (self.__class__.__name__, self.type, self.topic, self.body, self.headers)

    def unicode(self):
        return '%s %s %s %s' % (self.type, self.topic, self.body, self.headers)    

    def __str__(self):
        #return self.unicode().encode('ascii', 'replace')
        return self.unicode()
        



class DiffusionProtocol(WebSocketClientProtocol):

    _DELIMITERS_RECORD = '\x01'
    _DELIMITERS_FIELD = '\x02'
    _DELIMITERS_HANDSHAKE = '\x03'
    _DELIMITERS_MESSAGE = '\x08'

    _ENCODINGS_NONE = '\x00'

    _TYPES_TOPIC_LOAD_MESSAGE = '\x14'
    _TYPES_DELTA_MESSAGE = '\x15'
    _TYPES_SUBSCRIBE = '\x16'
    _TYPES_PING_CLIENT = '\x19'
    _TYPES_TOPIC_STATUS_NOTIFICATION = '\x23'

    # This message must be sent as soon as a connection is established.
    # {\x23}{\x03}P{\x01}_time,S_{SESSION_ID}{\x00}
    _MESSAGES_SESSION_ID = '%s%sP%s__time,S_%%s%s' % (
        _TYPES_TOPIC_STATUS_NOTIFICATION,
        _DELIMITERS_HANDSHAKE,
        _DELIMITERS_RECORD,
        _ENCODINGS_NONE,
    )

    # This message must be sent as soon as our session ID is acknowledged.
    # {\x16}{\x00}{TOPIC}{\x01}
    _MESSAGES_SUBSCRIPTION = '%s%s%%s%s' % (_TYPES_SUBSCRIBE, _ENCODINGS_NONE, _DELIMITERS_RECORD)

    def onOpen(self):
        self.factory.message_handler.post_connect()
        print('opened connection')
        if self.factory.session_id:
            message = self._MESSAGES_SESSION_ID % self.factory.session_id
            self._send(message)

    def onClose(self, was_clean, code, reason):
        print('closed connection')
        print('was clean: ', repr(was_clean))
        print('code: ', repr(code))
        print('reason: ', repr(reason))

    def onMessage(self, payload, isBinary):
        #self.factory.message_handler.pre_message()
        #print('received messages: ', repr(payload))
        messages = payload.decode().split(self._DELIMITERS_MESSAGE)
        while len(messages):
            message = messages.pop()
            type = message[0]
            if type == self.factory.trigger:
                for topic in self.factory.topics:
                    #print('send messages: ', (self._MESSAGES_SUBSCRIPTION % topic))
                    self._send(self._MESSAGES_SUBSCRIPTION % topic)
                continue
            if type in [self._TYPES_TOPIC_LOAD_MESSAGE, self._TYPES_DELTA_MESSAGE]:
                type = ord(type)
                records = message.split(self._DELIMITERS_RECORD)
                headers = records[0].split(self._DELIMITERS_FIELD)
                header = headers.pop()
                topic = header[1:]
                body = message[(len(records[0]) + 1):]
                self.factory.message_handler.post_message(DiffusionMessage(type, topic, body, headers))
                continue

    def _send(self, message):
        print('sending message:', repr(message))
        self.sendMessage(message.encode('utf-8'))
