import logging
import sys

# Custom formatter -- courtesy of : https://stackoverflow.com/questions/14844970/modifying-logging-message-format-based-on-message-logging-level-in-python3
class MyFormatter(logging.Formatter):

    error_fmt  = "ERROR: %(msg)s"
    debug_fmt  = "DBG: %(module)s: %(lineno)d: %(msg)s"
    info_fmt = "%(msg)s"
    warn_fmt = '%(levelname)s>\t%(message)s'

    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')  
    
    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = MyFormatter.debug_fmt

        elif record.levelno == logging.INFO:
            self._style._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._style._fmt = MyFormatter.error_fmt

        elif record.levelno == logging.WARNING:
            self._style._fmt = MyFormatter.warn_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result

def set_logging_level(level):
    fmt = MyFormatter()
    hdlr = logging.StreamHandler(sys.stdout)

    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(level)