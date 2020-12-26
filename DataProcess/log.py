# -*- coding: utf-8 -*-
"""Basic log-handling functions."""


import os
import json
import main
ENCODING = main.ENCODING


def auto_read_log(log_path, mode='r', encoding=ENCODING):
    """Automatically read and load a specified .json log."""
    if os.path.exists(log_path):
        with open(log_path, mode=mode, encoding=encoding) as fr:
            log = json.load(fr)
            fr.close()
    else:
        log = {}
    return log


def auto_write_log(log, log_path, mode='w', encoding=ENCODING):
    """Automatically write log into a .json file."""
    if not os.path.exists(os.path.split(log_path)[0]):
        os.makedirs(os.path.split(log_path)[0])
    with open(log_path, mode=mode, encoding=encoding) as fw:
        # Set ensure_ascii to False so that some special characters (non-English) can be encoded directly.
        json.dump(log, fw, ensure_ascii=False)
        fw.close()
    return


def rewrite_log(log_path, encoding=ENCODING):
    """Rewrite the existing log to be not-done ('N') for all items."""
    if os.path.exists(log_path):
        with open(log_path, mode='r', encoding=encoding) as fr:
            log = json.load(fr)
            fr.close()
        with open(log_path, mode='w', encoding=encoding) as fw:
            log.update([(key, 'N') for key in log.keys()])
            json.dump(log, fw, ensure_ascii=False)
            fw.close()
    return