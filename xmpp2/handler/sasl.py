import logging
import base64
from uuid import uuid4
from hashlib import md5
from xmpp2.model import XML

NS_SASL = 'urn:ietf:params:xml:ns:xmpp-sasl'


class DigestMD5(object):

    def __init__(self, client, username, password):
        self.client = client
        self.username = username
        self.password = password
        self.state = 0
        self.is_done = False

    def handle(self, xml_obj):
        if self.state == 0:
            challenge = base64.b64decode(xml_obj.text)
            logging.debug(challenge)
            digest = RFC2831(challenge).get_challenge()
            response = digest.get_response(self.username, self.password)
            response_b64 = base64.b64encode(str(response))
            self.write(XML.response(xmlns=NS_SASL).add(response_b64))
            self.state = 1
            self.client.process()
        elif self.state == 1:
            if xml_obj.tag.endswith('success'):
                rspauth = base64.b64decode(xml_obj.text)
                self.rspauth = rspauth.lstrip('rspauth=')
                self.is_done = True
                return self.PlugOut()
            elif xml_obj.tag.endswith('challenge'):
                rspauth = base64.b64decode(xml_obj.text)
                self.rspauth = rspauth.lstrip('rspauth=')
                self.write('<response xmlns="%s"/>' % NS_SASL)
                self.state = 2
                self.client.process()
            elif xml_obj.tag.endswith('failure'):
                raise Exception('Auth failure', xml_obj)
            else: pass
        elif self.state == 2:
            self.is_done = True
            return self.PlugOut()
        else:
            return # exit

    def write(self, s):
        self.client.write(s)

    class PlugOut(object):

        def act(self, client, handler):
            # Re-initiate for success.
            client.initiate()
            # Since this is a new stream, I need a new generator.
            client._create_generator()
            client.remove_handler(handler)


def H(*args):
    """
    >>> H() == md5('').digest()
    True
    >>> H('') == md5('').digest()
    True
    >>> H('a', 'b', 'c') == md5('a:b:c').digest()
    True
    """
    return md5(':'.join(args)).digest()


def KD(k, *args):
    """
    >>> KD('a', 'b', 'c') == H('a:b:c')
    True
    """
    return H(k, ':'.join(args))


def HEX(*args):
    return md5(':'.join(args)).hexdigest()


# def HMAC(k, s):
#     import hmac
#     return hmac(k, s).digest()


class RFC2831(object):

    def __init__(self, s):
        self.s = s

    def get_challenge(self):
        pairs = {}
        for x in self.s.split(','):
            key, value = x.split('=', 1)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            pairs[key] = value
        return DigestChallenge(**pairs)


class DigestChallenge(object):

    def __init__(self, realm=None, nonce=None, qop=None, stale=False,
                 maxbuf=65536, charset='iso-8859-1', algorithm=None,
                 cipher=None, should_log=False):
        self.realm = realm
        self.nonce = nonce
        self.qop = qop
        self.stale = stale
        self.maxbuf = maxbuf
        self.charset = charset
        self.algorithm = algorithm
        self.cipher = cipher
        self.should_log = should_log

    def get_response(self, username, password, nc=1, service_type='xmpp',
                     service_name=None):
        # H(s) = md5(s) 16 octet
        # KD(k, s) = H(k ':' s)
        # HEX(n) = md5(s) 32 hex digits (lower case)
        # HMAC(k, s) = hmac-md5(k, s)
        # response = HEX( KD( HEX( H(A1) ),
        #                     nonce ':' nc ':' cnonce ':' qop ':' HEX(H(A2))))
        # A1 = H( username ':' realm ':' password ) ':' nonce ':' cnonce
        #      [ ':' authzid ]
        # if qop == 'auth':
        #     A2 = 'AUTHENTICATE:' digest_uri
        # elif qop in ('auth-int', 'auth-conf'):
        #     A2 = 'AUTHENTICATE:' digest_uri ':' ('0' * 32)
        cnonce = base64.b64encode(uuid4().get_hex() + uuid4().get_hex())
        digest_uri = '%s/%s' % (service_type, self.realm)
        if service_name is not None:
            digest_uri += '/%s' % service_name

        A1 = (H(username, self.realm, password) + ':' + self.nonce + ':' +
              cnonce)
        self.log('username=%s realm=%s', username, self.realm)
        if self.qop == 'auth':
            A2 = 'AUTHENTICATE:%s' % digest_uri
        elif self.qop in ('auth-int', 'auth-conf'):
            A2 = 'AUTHENTICATE:%s:%s' % (digest_uri, '0' * 32)
        self.log('digest-uri=%s', digest_uri)
        response = HEX(HEX(A1), self.nonce, '%08x' % nc, cnonce, self.qop,
                       HEX(A2))
        self.log(response)
        return DigestResponse(username, self.realm, cnonce, nc, self.nonce,
                              digest_uri, response, self.charset, self.qop)

    def log(self, message, level=logging.DEBUG, *args, **kwargs):
        if self.should_log:
            logging.log(level, message, *args, **kwargs)


class DigestResponse(object):

    def __init__(self, username, realm, cnonce, nc, nonce, digest_uri,
                 response, charset, qop, authzid=None):
        self.username = username
        self.realm = realm
        self.cnonce = cnonce
        self.nc = nc
        self.nonce = nonce
        self.digest_uri = digest_uri
        self.response = response
        self.charset = charset
        self.qop = qop
        self.authzid = authzid

    def __str__(self):
        x = dict(self.__dict__)
        if x['authzid'] is None:
            del x['authzid']
        return (('charset=%s,username="%s",realm="%s",nonce="%s",nc=%08x,'
                 'cnonce="%s",digest-uri="%s",response=%s,qop=%s') %
                (self.charset, self.username, self.realm, self.nonce,
                 self.nc, self.cnonce, self.digest_uri, self.response,
                 self.qop))
