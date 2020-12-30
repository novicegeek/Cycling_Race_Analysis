# -*- coding: utf-8 -*-


global_vars = {}


def set_value(key, value):
    global_vars[key] = value
    return


def get_value(key):
    try:
        return global_vars[key]
    except KeyError:
        return None


set_value('ENCODING', 'utf-8')
set_value('ROOT', r"D:\PKU\LuLab\Masters'Thesis\Data")
