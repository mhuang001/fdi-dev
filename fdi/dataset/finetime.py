# -*- coding: utf-8 -*-
from .serializable import Serializable
from .eq import DeepEqual
from .copyable import Copyable
# from .metadata import ParameterTypes

from ..utils import leapseconds
import datetime
from string import ascii_uppercase
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

    * It has better resolution(microseconds);
    * ime differences are correct across leap seconds
    * It is immutable unless its TAI is 0..
    """

    """ The starting date in UTC """
    EPOCH = datetime.datetime(1958, 1, 1, 0, 0, 0, tzinfo=utcobj)

    """ number of TAI units in a second """
    RESOLUTION = 1000000  # microseconds

    """ The earliest time when valid leapsecond is used."""
    UTC_LOW_LIMIT = datetime.datetime(1972, 1, 1, 0, 0, 0, tzinfo=utcobj)

    UTC_LOW_LIMIT_TIMESTAMP = UTC_LOW_LIMIT.timestamp()

    """ Format used when not specified."""
    DEFAULT_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'  # ISO

    DEFAULT_FORMAT_SECOND = '%Y-%m-%dT%H:%M:%S'

    RETURNFMT = '%s.%06d'

    """ """
    TIMESPEC = 'microseconds'

    def __init__(self, date=None, format=None, **kwds):
        """ Initiate with a UTC date or an integer TAI.

        :date: time to be set to. Acceptable types: 

          * `int` for TAI,
          * `float`, `double` for UNIX time-stamp,
          * `datetime.datetime`,
          * `string` for ISO format date-time, 
          * bytes-like classes that can get string by calling its `decode(encoding='utf-8')`
        :format: ISO-8601 or some variation of it. Default is
`DEFAULT_FORMAT` and `DEFAULT_FORMAT_SECOND`.
        """

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
'0' and b'0' are taken as TAI=0.
        If a float is given, it will be taken as the `time` time stamp (UTC).
        If a datetime object or a string code is given, the timezone will be set to UTC.
        A FineTime instance is immutable except when TAI == 0. Violation gets a TypeError.
        """
        # setting to an impossible value
        setTai = ...
        if time is None:
            setTai = None
        elif issubclass(time.__class__, int):
            setTai = time
        elif issubclass(time.__class__, float):
            if time < self.UTC_LOW_LIMIT_TIMESTAMP:
                logger.warn(
                    'Timestamp before %s not defined yet.' % str(self.UTC_LOW_LIMIT_TIMESTAMP))
            d = datetime.datetime.fromtimestamp(time, tz=utcobj)
            setTai = self.datetimeToFineTime(d)
        elif issubclass(time.__class__, datetime.datetime):
            if time.tzinfo is None:
                d = time.replace(tzinfo=utcobj)
            else:
                d = time
            setTai = self.datetimeToFineTime(d)
        elif issubclass(time.__class__, (str, bytes)):
            t = time.strip()
            if issubclass(t.__class__, bytes):
                t = t.decode('ascii')
            fmt = self.format
            if fmt:
                try:
                    d = datetime.datetime.strptime(t, fmt)
                    d1 = d.replace(tzinfo=utcobj)
                    setTai = self.datetimeToFineTime(d1)
                except ValueError:
                    pass
        else:
            msg = ('%s must be an integer,a datetime object,'
                   'or a string or bytes or float, but its type is %s.' % (
                       str(time), type(time).__name__))
            raise TypeError(msg)
        if setTai is ...:
            # Now t has a date-time string in it.
            msg = '%s is not an integer or `datetime`' % t
            fmt = FineTime.DEFAULT_FORMAT
            try:
                d = datetime.datetime.strptime(t, fmt)
            except ValueError:
                msg += '\n%s does not match %s.' % (t, fmt)
                fmt = FineTime.DEFAULT_FORMAT_SECOND
                try:
                    d = datetime.datetime.strptime(t, fmt)
                except ValueError:
                    msg += '\n%s does not match %s.' % (t, fmt)
                    if ' ' in t:
                        fmt = FineTime.DEFAULT_FORMAT + ' %Z'
                        try:
                            d = datetime.datetime.strptime(t, fmt)
                            gotit = 2
                        except ValueError:
                            msg += '\n%s does not match %s.' % (t, fmt)
                            fmt = FineTime.DEFAULT_FORMAT + ' %z'
                            try:
                                d = datetime.datetime.strptime(t, fmt)
                                gotit = 2
                            except ValueError:
                                msg += '\n%s does not match %s.' % (t, fmt)
                                raise ValueError(msg)
                        logger.warning('Time zone %s assumed for %s' %
                                       (t.rsplit(' ')[1], t))
                    else:
                        # No ' ' in time string
                        gotit = False
                        if t.endswith('Z'):
                            fmt = FineTime.DEFAULT_FORMAT + 'Z'
                            try:
                                d = datetime.datetime.strptime(t, fmt).replace(
                                    tzinfo=utcobj)
                                gotit = 2
                            except ValueError:
                                msg += '\n%s does not match %s.' % (t, fmt)
                                fmt = FineTime.DEFAULT_FORMAT_SECOND + 'Z'
                                try:
                                    d = datetime.datetime.strptime(t, fmt).replace(
                                        tzinfo=utcobj)
                                    gotit = 2
                                except ValueError:
                                    msg += '\n%s does not match %s.' % (t, fmt)
                                pass
                        if not gotit:
                            # not ending with 'Z' or not match fmt+'Z'
                            fmt = FineTime.DEFAULT_FORMAT + '%Z'
                            try:
                                d = datetime.datetime.strptime(t, fmt)
                            except ValueError:
                                msg += '\n%s does not match %s.' % (t, fmt)
                                fmt = FineTime.DEFAULT_FORMAT + '%z'
                                try:
                                    d = datetime.datetime.strptime(t, fmt)
                                except ValueError:
                                    msg += '\n%s does not match %s.' % (t, fmt)
                                    raise TypeError(msg)
                    if gotit != 2:
                        logger.warning('Time zone %s taken for %s' %
                                       (str(d.tzname()), t))
            d1 = d.replace(tzinfo=utcobj) if d.tzinfo != utcobj else d
            setTai = self.datetimeToFineTime(d1)
        # setTai has a value
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

    @ classmethod
    def datetimeToFineTime(cls, dtm):
        """DateTime to FineTime conversion.

        Return given Python Datetime in FineTime to the precision of
        the input. Rounded to the last digit. Unit is decided by
        RESOLUTION.

        Parameters
        ----------
        cls : class
        dtm : DateTime
            Must be time-zone aware.

        Returns
        -------
        FineTime
            converted.

        """

        if dtm < cls.UTC_LOW_LIMIT:
            logger.warning(
                'UTC before %s not defined yet.' % str(cls.UTC_LOW_LIMIT))
        leapsec = leapseconds.dTAI_UTC_from_utc(dtm)
        sec = cls.RESOLUTION * ((dtm - cls.EPOCH + leapsec).total_seconds())
        return int(sec+0.5)

    def toDatetime(self, tai=None):
        """ Return given FineTime as a Python Datetime.

        tai: if not given or given as `None`, return this object's time as a Python Datetime.
        """
        if tai is None:
            tai = self.tai
        if tai is None:
            return None
        tai_time = datetime.timedelta(seconds=(float(tai) / FineTime.RESOLUTION)) \
            + FineTime.EPOCH
        # leapseconds is offset-native
        leapsec = leapseconds.dTAI_UTC_from_tai(tai_time)
        return tai_time - leapsec

    # HCSS compatibility
    toDate = toDatetime

    def isoutc(self, format='%Y-%m-%dT%H:%M:%S.%f'):
        """ Returns a String representation of this objet in ISO format without timezone. sub-second set to TIMESPEC.

        If `tai is None` return `''`.
        ;format: time format. default '%Y-%m-%dT%H:%M:%S' prints like 2019-02-17T12:43:04.577000 """
        if self.tai is None:
            return 'Unknown'

        dt = self.toDatetime(self.tai)
        return dt.strftime(format)

    def toString(self, level=0,  width=0, **kwds):
        """ Returns a String representation of this object according to self.format.
        level: 0 prints like 2019-02-17T12:43:04.577000 TAI(...)
        width: if non-zero, insert newline to break simplified output into shorter lines. For level=0 it is ``` #TODO ```

        """
        tais = str(self.tai) if hasattr(
            self, 'tai') and self.tai is not None else 'Unknown'
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

    string = toString
    txt = toString

    def __repr__(self):
        return self.toString(level=2)

    def __bool__(self):
        """ `True` if `tai > 0`.

        For `if` etc
        """
        return bool(self.tai)

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

    def __eq__(self, obj, **kwds):
        """ fast comparison using TAI. """

        if obj is None or not hasattr(self, 'tai') or not hasattr(obj, 'tai'):
            return False

        if id(self) == id(obj):
            return True

        if type(self) != type(obj):
            return False
        return self.tai == obj.tai

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
                           format=self.format)


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

    @ classmethod
    def datetimeToFineTime(cls, dtm):

        sec = (FineTime.datetimeToFineTime(dtm) -
               cls.TAI_AT_EPOCH) / FineTime.RESOLUTION
        # for subclasses with a different epoch
        return int(sec * cls.RESOLUTION + 0.5)

    def toDatetime(self, tai=None):

        if tai is None:
            tai = self.tai
        return super().toDatetime(tai * self.relative_res + self.TAI_AT_EPOCH)
