import uos
import sys

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_stream = sys.stderr

class Logger:

    def __init__(self, name):
        self.level = NOTSET
        self.name = name

    def _level_str(self, level):
        if level in _level_dict:
            return _level_dict[level]
        return "LVL" + str(level)

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            print(("%s:%s:" + msg) % ((self._level_str(level), self.name) + args), file=_stream)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)


class FileLogger(Logger):
    """Class for logging to a file"""
    def __init__(self, name):
        super().__init__(name)
        self.prefix = 'LOG'
        self.max_log_size = 1000
        self.current_log = '{}.{}'.format(self.prefix, 1)
        self.last_log = '{}.{}'.format(self.prefix, 2)
        self.fh = open(self.current_log,'w')

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            if self._logIsFull():
                self._rotateLogs()
            print(("%s:%s:" + msg) % ((self._level_str(level), self.name) + args), file=self.fh)

    def _logIsFull(self):
        self.fh.flush()
        if self.fh.tell() >= self.max_log_size:
            return True
        return False

    def _rotateLogs(self):
        """Don't have rename function in my micropython build"""
        self.fh.close()
        if self.exists(self.last_log):
            uos.unlink(self.last_log)
        #uos.rename(self.current_log, self.last_log)
        self.fh = open(self.current_log, mode='w')

    @staticmethod
    def exists(fpath):
        try:
            # Can't find where the docs/code to interpret return value is
            status = uos.stat(fpath)
        except OSError as e:
            return False
            #print(e.args[0] == uerrno.ENOENT)
        return True

_level = INFO
_loggers = {}
_logger_cls = Logger

def getLogger(name):
    global _logger_cls
    if name in _loggers:
        return _loggers[name]
    #l = Logger(name)
    l = _logger_cls(name)
    _loggers[name] = l
    return l

def info(msg, *args):
    getLogger(None).info(msg, *args)

def debug(msg, *args):
    getLogger(None).debug(msg, *args)

def basicConfig(level=INFO, filename=None, stream=None, format=None):
    global _level, _stream, _logger_cls
    _level = level
    if stream:
        _stream = stream
    # if filename is not None:
    #     print("logging.basicConfig: filename arg is not supported")
    if filename is not None:
        _logger_cls = FileLogger
    if format is not None:
        print("logging.basicConfig: format arg is not supported")
