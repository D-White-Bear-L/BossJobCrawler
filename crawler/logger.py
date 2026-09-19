# -*- coding: utf-8 -*-
"""终端 + 文件日志。格式对齐需求文档第十九节（[INFO] / [ERROR]）。"""
import os
import sys
import datetime

from config import LOG_DIR

_LOGFILE = None


def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _get_logfile():
    global _LOGFILE
    if _LOGFILE is None:
        _ensure_dir()
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(LOG_DIR, f"crawl_{stamp}.log")
        _LOGFILE = open(path, "a", encoding="utf-8")
    return _LOGFILE


def log(level, msg):
    """level: INFO / WARN / ERROR"""
    line = f"[{level}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        # Windows GBK 控制台打印中文异常时兜底
        try:
            print(line.encode("utf-8", "replace").decode("utf-8"), flush=True)
        except Exception:
            pass
    try:
        _get_logfile().write(line + "\n")
        _get_logfile().flush()
    except Exception:
        pass


def info(msg):
    log("INFO", msg)


def warn(msg):
    log("WARN", msg)


def error(msg):
    log("ERROR", msg)
