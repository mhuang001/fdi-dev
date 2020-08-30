# -*- coding: utf-8 -*-
from .serializable import Serializable
from .odict import ODict
from .eq import DeepEqual
from .copyable import Copyable
#from .metadata import ParameterTypes
import datetime
from collections import OrderedDict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


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
    """ Atomic time (SI seconds) elapsed since the TAI epoch
    of 1 January 1958 UT2. The resolution is one microsecond and the
    allowable range is: epoch + /-290, 000 years approximately.

    This has the following advantages, compared with the standard class:

    It has better resolution(microseconds)
    Time differences are correct across leap seconds
    It is immutable
    """

    EPOCH = datetime.datetime(1958, 1, 1, 0, 0, 0, tzinfo=utcobj)
    RESOLUTION = 1000000  # microsecond
    DEFAUL_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'  # ISO

    def __init__(self, date=None, format=None, **kwds):
        """ Initiate with a UTC date or an integer TAI"""
        leapsec = 0  # leap seconds to be implemented

        self.format = self.DEFAUL_FORMAT if format is None else format
        self.setTime(date)
        # logger.debug('date= %s TAI = %d' % (str(date), self.tai))
        super(FineTime, self).__init__(**kwds)

    @property
    def time(self):
        return self.getTime()

    @time.setter
    def time(self, time):
        self.setTime(time)

    def getTime(self):
        """ Returns the time related to this object."""
        return self.tai

    def setTime(self, time):
        """ Sets the time of this object. """
        if time is None:
            self.tai = 0
        elif issubclass(time.__class__, int):
            self.tai = time
        elif issubclass(time.__class__, datetime.datetime):
            if time.tzinfo is None:
                d = time.replace(tzinfo=utcobj)
            else:
                d = time
            self.tai = self.datetimeToFineTime(d)
        elif issubclass(time.__class__, str):
            # try:
            #     # TODO: xxx
            #     self.tai = int(time)
            # except ValueError:
            d = datetime.datetime.strptime(time, self.format)
            self.tai = self.datetimeToFineTime(d)
        else:
            raise TypeError('%s must be an integer, a datetime object, or a string, but its type is %s.' % (
                str(time), type(time).__name__))

    def getFormat(self):
        return self.format

    def __format__(self, format=None):
        """ Returns a String representation of this object according to format.
        Defaul format is self.format.
        prints like 2019-02-17T12:43:04.577000 """
        if format is None:
            format = self.format
        dt = datetime.timedelta(
            seconds=(self.tai / self.RESOLUTION)) + self.EPOCH
        # return dt.isoformat(timespec='microseconds')
        return dt.strftime(format)

    def microsecondsSinceEPOCH(self):
        """ Return the rounded integer number of microseconds since the epoch: 1 Jan 1958. """
        return int(self.tai * self.RESOLUTION / FineTime.RESOLUTION+0.5)

    def subtract(self, time):
        """ Subract the specified time and return the difference
        in microseconds. """
        return self.tai - time.tai

    @classmethod
    def datetimeToFineTime(cls, dtm):
        """ Return given  Python Datetime as a FineTime. """
        leapsec = 0  # leap seconds to be implemented
        return int(cls.RESOLUTION *
                   ((dtm - cls.EPOCH).total_seconds() + leapsec)+0.5)

    @classmethod
    def toDatetime(cls, tai):
        """ Return given FineTime as a Python Datetime. """
        leapsec = 0  # leap seconds to be implemented
        return datetime.timedelta(seconds=(float(tai) / cls.RESOLUTION - leapsec))\
            + cls.EPOCH

    def toDate(self):
        """ Return this time as a Python Datetime. """

        return self.toDatetime(self.tai)

    def toString(self):
        """ Returns a String representation of this object according to self.format.
        prints like 2019-02-17T12:43:04.577000 TAI(...)"""

        return self.__format__() + ' TAI' + '(%d)' % (self.tai)

    def equals(self, obj):
        """ can compare TAI directly """
        if 1:
            return self.tai == obj
        else:
            return super(FineTime, self).equals(obj)

    def __lt__(self, obj):
        """ can compare TAI directly """
        if 1:
            # if type(obj).__name__ in ParameterTypes.values():
            return self.tai < obj
        else:
            return super(FineTime, self).__lt__(obj)

    def __gt__(self, obj):
        """ can compare TAI directly """
        if 1:
            # if type(obj).__name__ in ParameterTypes.values():
            return self.tai > obj
        else:
            return super(FineTime, self).__gt__(obj)

    def __le__(self, obj):
        """ can compare TAI directly """
        if 1:
            # if type(obj).__name__ in ParameterTypes.values():
            return self.tai <= obj
        else:
            return super(FineTime, self).__le__(obj)

    def __ge__(self, obj):
        """ can compare TAI directly """
        if 1:
            # if type(obj).__name__ in ParameterTypes.values():
            return self.tai >= obj
        else:
            return super(FineTime, self).__ge__(obj)

    def __repr__(self):
        return self.toString()

    def __str__(self):
        return self.toString()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(tai=self.tai,
                           format=self.format,
                           classID=self.classID)


class FineTime1(FineTime):
    """ Same as FineTime but Epoch is 2017-1-1 0 UTC """
    EPOCH = datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=utcobj)
    RESOLUTION = 1000  # millisecond
