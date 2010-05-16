from uuid import uuid4
from hashlib import md5
import hmac
import base64
import logging


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


def HMAC(k, s):
    return hmac(k, s).digest()


class RFC2831(object):

    def __init__(self, s):
        self.s = s

    def get_challenge(self):
        pairs = {}
        for x in self.s.split(','):
            key, value = x.split('=', 2)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            pairs[key] = value
        logging.debug(pairs)
        return DigestChallenge(**pairs)


class DigestChallenge(object):

    def __init__(self, realm=None, nonce=None, qop=None, stale=False,
                 maxbuf=65536, charset='iso-8859-1', algorithm=None,
                 cipher=None):
        self.realm = realm
        self.nonce = nonce
        self.qop = qop
        self.stale = stale
        self.maxbuf = maxbuf
        self.charset = charset
        self.algorithm = algorithm
        self.cipher = cipher

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
        logging.debug('username=%s realm=%s', username, self.realm)
        if self.qop == 'auth':
            A2 = 'AUTHENTICATE:%s' % digest_uri
        elif self.qop in ('auth-int', 'auth-conf'):
            A2 = 'AUTHENTICATE:%s:%s' % (digest_uri, '0' * 32)
        logging.debug('A2: %s', A2)
        response = HEX(HEX(A1), self.nonce, '%08x' % nc, cnonce, self.qop,
                       HEX(A2))
        logging.debug(response)
        return DigestResponse(username, self.realm, cnonce, nc, self.nonce,
                              digest_uri, response, self.charset, self.qop)


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
