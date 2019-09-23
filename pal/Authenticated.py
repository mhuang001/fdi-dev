# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Authenticated(self):
    """
    for items supporting user authentication.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._authstring = None
        self._authenticationRequired = False

    def getAuthString(self):
        """
        Get a Base 64 encoded authorisation string suitable for network transmission or saving.
        """
        return self._authstring

    def getUniqueId(self):
        """
        Get an id for this that can uniquely identify it for authentication purposes.
        """

    def isAuthenticationRequired(self):
        """
        Is this configured to require authentication?
        """
        return self._authenticationRequired

    def setAuthentication(self, authString, username='',  password=''):
        """
        Set the user authentication details for access.
        mh: if one positional arg is given it is taken as the authString.
        if the authString is not None and not empty, username and password are ignored.
        """
        if authString is not None and authString != '':
            self._authstring = authString
            return
        up = bytes((username + ':' + password).encode('ascii'))
        code = base64.b64encode(up).decode("ascii")
        self._authstring = code
        return

    def setAuthenticationRequired(self, required):
        """
        Explicitly set the pool to require, or not require authentication.
        """
        self._authenticationRequired = required
