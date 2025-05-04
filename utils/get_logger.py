import inspect
import logging
import os


def get_logger()->logging.Logger:
    caller_module = inspect.currentframe().f_back.f_globals["__name__"]
    logger = logging.getLogger(caller_module)
    logger.setLevel(logging.DEBUG)

    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{caller_module}.log")
    fmt = "[{levelname}] [{asctime} {module}]:[{lineno}] [{funcName}] [{message}]"
    
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in logger.handlers):
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, style="{"))
        logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(fmt=fmt, style="{"))
        logger.addHandler(stream_handler)

    return logger
