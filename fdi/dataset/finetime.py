# -*- coding: utf-8 -*-
import datetime

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


from .copyable import Copyable
from .eq import DeepEqual
from .odict import ODict
from .serializable import Serializable

# A UTC class.


class UTC(datetime.tzinfo):
    """UTC
    https://docs.python.org/2.7/library/datetime.html?highlight=datetime#datetime.tzinfo
    """

    ZERO = datetime.timedelta(0)
    HOUR = datetime.timedelta(hours=1)

    def utcoffset(self, dt):
        return UTC.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return UTC.ZERO


utcobj = UTC()


class FineTime(Copyable, DeepEqual, Serializable):
    """ Atomic time(SI seconds) elapsed since the TAI epoch
    of 1 January 1958 UT2. The resolution is one microsecond and the
    allowable range is: epoch + /-290, 000 years approximately.

    This has the following advantages, compared with the standard class:

    It has better resolution(microseconds)
    Time differences are correct across leap seconds
    It is immutable
    """

    EPOCH = datetime.datetime(1958, 1, 1, 0, 0, 0, tzinfo=utcobj)
    RESOLUTION = 1000000  # microsecond

    def __init__(self, date=None, **kwds):
        """ Initiate with a UTC date """
        leapsec = 0  # leap seconds to be implemented
        if date is None:
            self.tai = 0
        else:
            if date.tzinfo is None:
                d = date.replace(tzinfo=utcobj)
            else:
                d = date
            self.tai = self.RESOLUTION * \
                ((d - self.EPOCH).total_seconds() + leapsec)
        # logger.debug('date= %s TAI = %d' % (str(date), self.tai))
        super(FineTime, self).__init__(**kwds)

    def microsecondsSinceEPOCH(self):
        """ Return the number of microseconds since the epoch: 1 Jan 1958. """
        return self.tai * (self.RESOLUTION / FineTime.RESOLUTION)

    def subtract(self, time):
        """ Subract the specified time and return the difference
        in microseconds. """
        return self.tai - time.tai

    def toDate(self):
        """ Return this time as a Python Date. """
        leapsec = 0  # leap seconds to be implemented
        return datetime.timedelta(seconds=(self.tai / self.RESOLUTION - leapsec))\
            + self.EPOCH

    def toString(self):
        """ Returns a String representation of this object.
        prints like 2019 - 02 - 17T12: 43: 04.577000 TAI """
        dt = datetime.timedelta(
            seconds=(self.tai / self.RESOLUTION)) + self.EPOCH
        # return dt.isoformat(timespec='microseconds')
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f TAI') +\
            '(%d)' % (self.tai)

    def __repr__(self):
        return self.toString()

    def __str__(self):
        return self.toString()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(tai=self.tai,
                     classID=self.classID,
                     version=self.version)


class FineTime1(FineTime):
    """ Same as FineTime but Epoch is 2017-1-1 0 UTC """
    EPOCH = datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=utcobj)
    RESOLUTION = 1000  # millisecond
