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

def try_pz(t, msg):
    for end in ('', '%Z', '%z'):
        for _f in (FineTime.DEFAULT_FORMAT,
                   FineTime.DEFAULT_FORMAT_SECOND):
            for sept in ('T', ' '):
                for sepz in ('', ' '):
                    if sept != 'T':                
                        _f = _f.replace('T', sept, 1)
                    fmt = f"{_f}{sepz}{end}"
                    try:
                        d = datetime.datetime.strptime(t, fmt)
                        gotit = 2
                        return gotit, fmt, d
                    except ValueError:
                        msg += '\n%s does not match %s.' % (t, fmt)
    if end:
        logger.warning('Time zone %s assumed for %s' %
                   (t.rsplit(' ')[1], t))
    return None, msg

                                    

def try_ends(t, ends, msg):
    for end in ends:
        if end == '':
            break
        for case in set((end, end.upper())):
            if t.endswith(case):
                for _f in (FineTime.DEFAULT_FORMAT,
                           FineTime.DEFAULT_FORMAT_SECOND):
                    fmt = f"{_f}{case}"
                    try:
                        d = datetime.datetime.strptime(t, fmt).replace(
                            tzinfo=utcobj)
                        gotit = 2
                        return gotit, fmt, d
                    except ValueError:
                        msg += '\n%s does not match %s.' % (t, fmt)
                        pass
    # not ending with case or not match fmt+case
        
    return try_pz(t, msg)

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

    """ The earliest time when valid leapsecond is used."""
    UTC_LOW_LIMIT = datetime.datetime(1972, 1, 1, 0, 0, 0, tzinfo=utcobj)

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

    def _float2settai(self, time):
        if time < self.UTC_LOW_LIMIT_TIMESTAMP:
            logger.warning(
                'Timestamp before %s not defined yet.' % str(self.UTC_LOW_LIMIT_TIMESTAMP))
        d = datetime.datetime.fromtimestamp(time, tz=utcobj)
        return self.datetimeToFineTime(d)

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
        If a float is given, it will be taken as the `time`
        time stamp (UTC).
        If a datetime object or a string code is given, the
        timezone will be set to UTC.
        A FineTime instance is immutable except when TAI == 0.
        Violation gets a `TypeError`.
        """
        fmt = self.format
        # setting to an impossible value
        setTai = ...
        if time is None or time == 'None':
            self.tai = None
            return
        # def default_conv(t):
        #     if t.tzinfo is None:
        #         d = time.replace(tzinfo=utcobj)
        #     else:
        #         d = time
        #     return self.datetimeToFineTime(d)
        # def str_int(t):
        #     if issubclass(t.__class__, bytes):
        #         t = t.decode('ascii')
        #     try:
        #         setTai = int(t)
        #         # Do not return yet
        #     except ValueError:
        #         try:
        #             f = float(t)
        #             # unix timestamp
        #             self.tai = self._float2settai(f)
        #             return
        #         except ValueError:
        #             pass
        # def str_default_fmt(t):
        #                     # int works as tai but it would work better as something else
        #             # the most often case
        #             d = datetime.datetime.strptime(t, fmt)
        #             d1 = d.replace(tzinfo=utcobj)
        #             self.tai = self.datetimeToFineTime(d1)
        #             # possible result of int(time) setTai is overidden
        #             return
        #         except ValueError:
        #             # the time is a str and cannot be interpreted according to fmt
        #             # return the int if there has been one.
        #             if issubclass(setTai.__class__, int):
        #                 self.tai = setTai
        #                 return
        #  def str_datetime(t):
        #         try:
        #             # the most often case
        #             d = datetime.datetime.strptime(t, fmt)
        #             d1 = d.replace(tzinfo=utcobj)
        #             self.tai = self.datetimeToFineTime(d1)
        #             # possible result of int(time) setTai is overidden
        #             return
        #         except ValueError:
        #             # the time is a str and cannot be interpreted according to fmt
        #             # return the int if there has been one.
        #             if issubclass(setTai.__class__, int):
        #                 self.tai = setTai
        #                 return

        # cases = [(lambda t: issubclass(t.__class__, int), lambda t:t),
        #          (lambda t: issubclass(t.__class__, float), lambda t:self._float2settai(t)),
        #          (lambda t: issubclass(t.__class__, datetime.datetime), default_conv),
        #          (lambda t: issubclass(time.__class__, (str, bytes)), str_int),
        #          (lambda t: issubclass(time.__class__, datetime.datetime), str_datetime),
        #          (lambda t: issubclass(time.__class__, (str)), str_default_fmt),
                 
        #          ]
        # these can work without format
        if issubclass(time.__class__, int):
            self.tai = time
            return
        elif issubclass(time.__class__, FineTime):
            self.tai = time.tai
            return
        elif issubclass(time.__class__, float):
            self.tai = self._float2settai(time)
            return
        elif issubclass(time.__class__, datetime.datetime):
            if time.tzinfo is None:
                d = time.replace(tzinfo=utcobj)
            else:
                d = time
            self.tai = self.datetimeToFineTime(d)
            return
        elif issubclass(time.__class__, (str, bytes)):
            t = time
            if issubclass(t.__class__, bytes):
                t = t.decode('ascii')
            try:
                setTai = int(t)
                # Do not return yet
            except ValueError:
                try:
                    f = float(t)
                    # unix timestamp
                    self.tai = self._float2settai(f)
                    return
                except ValueError:
                    pass

            # int works as tai but it would work better as something else
            try:
                # the most often case
                d = datetime.datetime.strptime(t, fmt)
                d1 = d.replace(tzinfo=utcobj)
                self.tai = self.datetimeToFineTime(d1)
                # possible result of int(time) setTai is overidden
                return
            except ValueError:
                # the time is a str and cannot be interpreted according to fmt
                # return the int if there has been one.
                if issubclass(setTai.__class__, int):
                    self.tai = setTai
                    return
        else:    
            msg = ('%s must be an integer, a float, a datetime or FineTime object,'
                   'or a string or bytes or str/bytes of an int or float, '
                   'but its type is %s.' % (str(time), type(time).__name__))
            raise TypeError(msg)
        
        #setTai is either "..." or a string.
        if setTai is ...:
            d = None
            # Now t has a date-time string in it.
            msg = '%s is not an integer or `datetime` %s.' % (t, self.format)
            fmt = FineTime.DEFAULT_FORMAT
            try:
                d = datetime.datetime.strptime(t, fmt)
            except ValueError:
                msg += '\n%s does not match %s.' % (t, fmt)
                w = t.replace('-','').replace(':','').replace(' ','')
                tm = f'{w[:4]}-{w[4:6]}-{w[6:8]}T{w[8:10]}:{w[10:12]}:{w[12:]}'
                try:
                    d = datetime.datetime.strptime(tm, fmt)
                except ValueError:
                    msg += '\n%s does not match %s.' % (tm, fmt)
                    fmt = FineTime.DEFAULT_FORMAT_SECOND
                    try:
                        d = datetime.datetime.strptime(tm, fmt)
                    except ValueError:
                        msg += '\n%s does not match %s.' % (tm, fmt)
                        got = try_ends(t, ('', 'Z'), msg)
                        if got[0] is None:
                            gotit, msg = got
                        else:
                            gotit, fmt, d = got

                        if gotit != 2:
                            logger.warning('Time zone %s taken for %s' %
                                           ('?', t))
            if d is not None:
                d1 = d.replace(tzinfo=utcobj) if d.tzinfo != utcobj else d
                setTai = self.datetimeToFineTime(d1)
            # if d is None:
            # pat = re.compile(r'2(ddd)(-: /|\w)*([01]?d)(-: /|\w)([0123)?d)(-: /|\w)[012]?d(-: /|\w)[0-5]?d(-: /|\w)[0-6]f[[ Z]?[+-].*'

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
                'datetime before %s not defined.' % str(cls.UTC_LOW_LIMIT))
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


""" The mission T0. No leapsecond in 7 years."""
TAI2017 = FineTime().datetimeToFineTime(datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=utcobj))

""" The would-be starting time of UNIX timestamp."""
TAI1970 = FineTime().datetimeToFineTime(datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=utcobj))

