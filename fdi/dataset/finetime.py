# -*- coding: utf-8 -*-
from .serializable import Serializable
from .odict import ODict
from .eq import DeepEqual
from .copyable import Copyable
# from .metadata import ParameterTypes

from ..utils import leapseconds
import datetime
from collections import OrderedDict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


utcobj = datetime.timezone.utc


class FineTime(Copyable, DeepEqual, Serializable):
    """ Atomic time (SI seconds) elapsed since the TAI epoch
    of 1 January 1958 UT2. The resolution is one microsecond and the
    allowable range is: epoch + /-290, 000 years approximately.

    This has the following advantages, compared with the standard class:

    It has better resolution(microseconds)
    Time differences are correct across leap seconds
    It is immutable
    """
    """ Te starting date in UTC """
    EPOCH = datetime.datetime(1958, 1, 1, 0, 0, 0, tzinfo=utcobj)

    """ number of TAI units in a second """
    RESOLUTION = 1000000  # microsecond

    """ """
    UTC_LOW_LIMIT = EPOCH  # datetime.datetime(1972, 1, 1, 0, 0, 0, tzinfo=utcobj)

    """ """
    DEFAULT_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'  # ISO

    RETURNFMT = '%s.%06d'

    """ """
    TIMESPEC = 'microseconds'

    def __init__(self, date=None, format=None, **kwds):
        """ Initiate with a UTC date or an integer TAI"""

        self.format = FineTime.DEFAULT_FORMAT if format is None else format
        self.setTime(date)
        # logger.debug('date= %s TAI = %d' % (str(date), self.tai))
        super().__init__(**kwds)

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
        """ Sets the time of this object.

        If an integer is given, it will be taken as the TAI.
        If a datetime object or a string code is given, the timezone will be set to UTC.
        Only when current TAI is 0, so a non-zero instance is immutable. Violation gets a TypeError.
        """

        if not issubclass(time.__class__, int):
            pass
        if time is None:
            setTai = 0
        elif issubclass(time.__class__, int):
            setTai = time
        elif issubclass(time.__class__, datetime.datetime):
            if time.tzinfo is None:
                d = time.replace(tzinfo=utcobj)
            else:
                d = time
            setTai = self.datetimeToFineTime(d)
        elif issubclass(time.__class__, str):
            t = time.strip()
            try:
                d = datetime.datetime.strptime(t, self.format)
            except ValueError:
                if self.format[-4] == ' ':
                    # the last three letters are tz
                    tz = self.format[-3:]
                    if not t.endswith(tz):
                        logger.warning('Time zone %s assumed for %s', tz, t)
                        d = datetime.datetime.strptime(
                            t + ' ' + tz, self.format)
                else:
                    # format does not have tz
                    logger.warning(
                        'Time zone stripped for %s according to format.' % t)
                    d = datetime.datetime.strptime(
                        t.rsplit(' ', 1)[0], self.format)
            d1 = d.replace(tzinfo=datetime.timezone.utc)
            setTai = self.datetimeToFineTime(d1)
        else:
            raise TypeError('%s must be an integer, a datetime object, or a string, but its type is %s.' % (
                str(time), type(time).__name__))
        try:
            if setTai and self.tai:
                raise TypeError(
                    'FineTime objects with non-zero TAI are immutable.')
        except AttributeError:
            # self.tai not exists
            pass
        self.tai = setTai

    def getFormat(self):
        """ `format` cannot be a property name as it is a built so`@format.setter` is not allowed.
        """
        return self.format

    def microsecondsSinceEPOCH(self):
        """ Return the rounded integer number of microseconds since the epoch: 1 Jan 1958. """
        return int(self.tai * self.RESOLUTION / FineTime.RESOLUTION+0.5)

    def subtract(self, time):
        """ Subract the specified time and return the difference
        in microseconds. """
        return self.tai - time.tai

    @classmethod
    def datetimeToFineTime(cls, dtm):
        """ Return given  Python Datetime in FineTime to the precision of the input. Rounded to the last digit. Unit is decided by RESOLUTION."""
        if dtm < cls.UTC_LOW_LIMIT:
            raise NotImplemented(
                'UTC before %s not working yet.' % str(cls.UTC_LOW_LIMIT))
        leapsec = leapseconds.dTAI_UTC_from_utc(dtm)
        sec = cls.RESOLUTION * ((dtm - cls.EPOCH + leapsec).total_seconds())
        return int(sec+0.5)

    def toDatetime(self, tai=None):
        """ Return given FineTime as a Python Datetime.

        tai: if not given or given as `None`, return this object's time as a Python Datetime.
        """
        if tai is None:
            tai = self.tai

        tai_time = datetime.timedelta(seconds=(float(tai) / FineTime.RESOLUTION)) \
            + FineTime.EPOCH
        # leapseconds is offset-native
        leapsec = leapseconds.dTAI_UTC_from_tai(tai_time)
        return tai_time - leapsec

    # HCSS compatibility
    toDate = toDatetime

    def isoutc(self, format='%Y-%m-%dT%H:%M:%S.%f'):
        """ Returns a String representation of this objet in ISO format without timezone. sub-second set to TIMESPEC.

        format: time format. default '%Y-%m-%dT%H:%M:%S' prints like 2019-02-17T12:43:04.577000 """
        dt = self.toDatetime(self.tai)
        return dt.strftime(format)

    def toString(self, level=0,  width=0, **kwds):
        """ Returns a String representation of this object according to self.format.
        level: 0 prints like 2019-02-17T12:43:04.577000 TAI(...)
        width: if non-zero, insert newline to break simplified output into shorter lines. For level=0 it is ``` #TODO ```

        """
        tais = str(self.tai) if hasattr(self, 'tai') else 'Unknown'
        fmt = self.format
        if level == 0:
            if width:
                tstr = self.isoutc(format=fmt) + '\n' + tais
                s = tstr
            else:
                tstr = self.isoutc(format=fmt) + ' TAI(%s)' % tais
                s = tstr + ' format=' + self.format
        elif level == 1:
            if width:
                tstr = self.isoutc(format=fmt) + '\n%s' % tais
            else:
                tstr = self.isoutc(format=fmt) + ' (%s)' % tais
            s = tstr
        elif level == 2:
            if width:
                s = self.__class__.__name__ + '(' + \
                    self.isoutc(format=fmt).replace('T', '\n') + ')'
            else:
                s = self.__class__.__name__ + '(' + \
                    self.isoutc(format=fmt) + ')'
        else:
            s = tais
        return s

    def __repr__(self):
        return self.toString(level=2)

    def __bool__(self):
        """ `True` if `tai > 0`.  

        For `if` etc 
        """
        return self.tai > 0

    def __int__(self):
        return self.tai

    __index__ = __int__

    def __add__(self, obj):
        """ can add an integer as a TAI directly and return a new instance."""

        oc = obj.__class__
        sc = self.__class__
        if issubclass(oc, int):
            return sc(self.tai+obj, format=self.format)
        else:
            raise TypeError(
                f'{sc.__name__} cannot add/minus {oc.__name__} {obj}')

    def __sub__(self, obj):
        """ can minus an integer as a TAI directly and return a new instance,
        or subtract another FineTime instance and returns TAI difference in microseconds.
        """
        oc = obj.__class__
        sc = self.__class__
        if issubclass(oc, int):
            return sc(self.tai-obj, format=self.format)
        elif issubclass(oc, sc):
            return self.tai - obj.tai
        else:
            raise TypeError(f'{sc.__name__} cannot minus {oc.__name__} {obj}')

    def __iadd__(self, obj):
        """ can add an integer as a TAI directly to self like ```v += 3```."""

        oc = obj.__class__
        sc = self.__class__
        if issubclass(oc, int):
            self.tai += obj
        else:
            raise TypeError(f'{sc.__name__} cannot add/minus {oc} {obj}')

    def __isub__(self, obj):
        """ can subtract an integer as a TAI directly from self like ```v -= 3```."""

        oc = obj.__class__
        sc = self.__class__
        if issubclass(oc, int):
            self.tai -= obj
        else:
            raise TypeError(f'{sc.__name__} cannot add/minus {oc} {obj}')

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

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(tai=self.tai,
                           format=self.format,
                           _STID=self._STID)


class FineTime1(FineTime):
    """ Same as FineTime but Epoch is 2017-1-1 0 UTC and unit is millisecond"""
    EPOCH = datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=utcobj)
    RESOLUTION = 1000  # millisecond
    RETURNFMT = '%s.%03d'
    TIMESPEC = 'milliseconds'
    TAI_AT_EPOCH = FineTime.datetimeToFineTime(EPOCH)

    def __init__(self, *args, **kwds):

        self.relative_res = FineTime.RESOLUTION / float(self.RESOLUTION)
        super().__init__(*args, **kwds)

    @classmethod
    def datetimeToFineTime(cls, dtm):

        sec = (FineTime.datetimeToFineTime(dtm) -
               cls.TAI_AT_EPOCH) / FineTime.RESOLUTION
        # for subclasses with a different epoch
        return int(sec * cls.RESOLUTION + 0.5)

    def toDatetime(self, tai=None):

        if tai is None:
            tai = self.tai
        return super().toDatetime(tai * self.relative_res + self.TAI_AT_EPOCH)
