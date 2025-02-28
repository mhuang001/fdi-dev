# -*- coding: utf-8 -*-
from ..pal.urn import Urn


from ..dataset.odict import ODict
from ..dataset.eq import DeepEqual
from ..dataset.serializable import Serializable
from requests.auth import HTTPBasicAuth
from werkzeug.datastructures import Authorization

from collections import namedtuple, OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))



class Authenticatable(DeepEqual, Serializable):
    """
    Definition of services provided by a product storage supporting authentication.
    """
    
    def __init__(self, auth=None, username=None, password=None, token=None, authtype=None, **kwds):
        super().__init__(**kwds)
        if auth:
            self.setAuth(auth)
        elif token:
            self.setCredential(token)
        else:
            self.setAuth((username, password, authtype) if authtype \
                         else (username, password))

    @property
    def auth(self):
        """ for property getter
        """
        return self.getAuth()

    @auth.setter
    def auth(self, auth):
        """ for property setter
        """
        self.setAuth(auth)

    def getAuth(self):
        """ Gets the auth of this pool as an Object. """
        return self._auth

    def setAuth(self, auth):
        """ Replaces the current auth of this pool.
        """
        if issubclass(auth.__class__, (list, tuple)):
            if len(auth) == 2:
                self.authtype = 'HTTPBasicAuth'
                self.token = None
                self.setCredential((auth[0], auth[1], self.authtype))
            elif len(auth) == 3:
                self.setCredential(auth)
        elif issubclass(auth.__class__, str):
            self.setCredential(auth)
        else:
            self._auth = auth
            self.username = getattr(auth, 'username', None)
            self.password = getattr(auth, 'password', None)
            self.token = None
            self.authtype = auth.__class__.__name__

    @property
    def credential(self):
        """ for property getter
        """
        return self.getCredential()

    @credential.setter
    def credential(self, credential):
        """ for property setter
        """
        self.setCredential(credential)

    def getCredential(self):
        """ Gets the credential of this pool as an Object. """
        return self.__getstate__()['credential']
    
    def setCredential(self, cred):
        """set credentials and create the internal auth object.

        Parameters
        ----------
        cred : str, tuple, list
            [username, password, authtype] or token
         type : str
            id of authentication type.

        Returns
        -------
        None

        Examples
        --------
        FIXME: Add docs.


        """

        if issubclass(cred.__class__, str):
            token, authtype = cred, 'token'
            username, password = None, None
        elif issubclass(cred.__class__, (tuple, list)) and len(cred) == 3:
            username, password, authtype = tuple(cred)
            token = None
        else:
            raise TypeError("Input is a string or a 3-element list.")

        if  authtype == 'HTTPBasicAuth':
            self.auth = HTTPBasicAuth(username, password)
        elif authtype == 'Authorization':
            self.auth = Authorization(
                "basic", {"username": username, "password": password})
        elif authtype == 'token':
            self.token = token
        else:
            self.auth = cred


        self.username = username
        self.password = password
        self.authtype = authtype
        
    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        if hasattr(self, 'token') and self.token:
            return OrderedDict(
                credential = self.token
            )
        return OrderedDict(
            credential = [self.username,
                           self.password,
                           self.authtype,
                           ]
        )

