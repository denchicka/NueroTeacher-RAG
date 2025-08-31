import logging, os
from collections import deque
from typing import Deque

_buffer: Deque[str] = deque(maxlen=1500)

class BufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            _buffer.append(self.format(record))
        except Exception:
            pass

def get_buffer_text() -> str:
    return "\n".join(_buffer)

def get_logger(name: str = "neuroteacher", level: int = logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers: 
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
    sh = logging.StreamHandler(); sh.setFormatter(fmt); logger.addHandler(sh)
    bh = BufferHandler(); bh.setFormatter(fmt); logger.addHandler(bh)
    return logger
