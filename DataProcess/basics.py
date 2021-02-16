# -*- coding: utf-8 -*-
"""Some basic functions used in this package."""


import codecs
import os
import re
import numpy as np
import pandas as pd
import global_vars


ENCODING = global_vars.get_value('ENCODING')


def create_race_id(race_abbr, year, is_multi_stage, from_race_meta, stage=None, align=2):
    """
    Create ID for a stage/race, using the NOMINAL stage number.

    Format: abbr+year+code (for a whole race, the last part is set to 'R01', meaning 'Race No.1';
        a single-stage race will also be coded as 'R01').

    :param race_abbr: The full name of the race.
    :param year: The current year that's being examined.
    :param is_multi_stage: 1/0 or boolean.
    :param from_race_meta: 1/0 or boolean. Whether the stage information is from the race meta document,
        or from the results data file name.
    :param stage: The original stage code.
    :param align: The total number of characters for numbering the stage/race.
        By default 2, i.e., stage No.2 will be represented by 02.
    """
    if stage is None:
        print("    Warning: No valid stage information.")
        return np.nan
    elif from_race_meta:
        if is_multi_stage and not pd.isna(stage):
            try:
                number = str(int(stage))  # A normal stage in a multi-stage race or a single-stage race
                stage_code = 'S' + '0' * (align - len(number)) + number
            except ValueError:  # A Prologue stage
                stage_code = 'P01'
        else:  # The overall multi-stage race, not a single stage
            stage_code = 'R01'
    else:
        if 'S' in stage:
            stage_number = stage.split('S')[1]
            stage_code = 'S' + '0' * (align - len(stage_number)) + stage_number
        elif stage == 'FC':
            stage_code = 'R01'
        elif stage == 'P':
            stage_code = 'P01'
        else:
            print("    Warning: Invalid stage information.")
            return np.nan
    return race_abbr + str(year) + stage_code


def find_interval(endpoints, number, left_open=True, sort=False):
    endpoints = list(endpoints)
    if sort:
        endpoints.sort()
    for i in range(len(endpoints) - 1):
        if pd.isna(number):
            return None
        elif left_open and \
                (endpoints[i] < number <= endpoints[i+1] or (i == 0 and number == endpoints[i])):
            return i
        elif not left_open and \
                (endpoints[i] <= number < endpoints[i+1] or (i == len(endpoints) - 2 and number == endpoints[i])):
            return i
    return None


def get_file_list(file_dir, extension=None):
    """
    To extract the COMPLETE paths of all files belonging to a directory, including those in its subdirectories.

    :param file_dir: The root directory intended to be extracted from.
    :param extension: The format of files can be specified by their extensions; by default all files will be extracted.
    :return: List of file paths.
    """
    file_list = []
    for root, dirs, files in os.walk(file_dir):
        if extension:
            for file in files:
                if os.path.splitext(file)[1] == extension:
                    file_list.append(os.path.join(root, file))
        else:
            for file in files:
                file_list.append(os.path.join(root, file))
    return file_list


def is_number(s):
    """
    To determine whether a variable is a discernable "number" to human.

    :param s: E.g., inputting '123' or 123 will get you True, while inputting '1+2+3' will get you False.
    :return: Boolean True or False.
    :raise ValueError: This error occurs when the input can not be interpreted as a number in any sense.
    """
    try:
        if pd.isna(s):
            return False
        float(s)
        return True
    except ValueError:
        return False


def get_races_list(races):
    """Set the variable 'races' to be iterable according to the input value of the parameter."""
    if type(races) == str:
        if races == 'Grand Tour':
            races = global_vars.get_value('GRAND TOUR')
        elif races == 'all':
            races = global_vars.get_value('RACES')
        elif races == 'multi':
            races = global_vars.get_value('MULTI-STAGES')
        elif races == 'single':
            races = global_vars.get_value('SINGLE-STAGE')
        else:
            races = [races]
    else:
        pass
    return list(races)


def get_seasons_list(seasons):
    """Set the variable 'seasons' to be iterable according to the input value of the parameter."""
    if type(seasons) == str:
        if seasons == 'all':
            seasons = global_vars.get_value('SEASONS')
        else:
            seasons = [seasons]
    elif type(seasons) == int:
        seasons = [str(seasons)]
    else:
        seasons = [str(year) for year in seasons]
    return list(seasons)


def get_result_types_list(result_types):
    """Set the variable 'result_types' to be iterable according to the input value of the parameter."""
    if type(result_types) == str:
        result_types = [result_types]
    else:
        result_types = list(result_types)
    return result_types


def time2sec(time):
    """Transform an input time to a number indicating the corresponding second counts.

    :param time: The time to be converted. Can be a string, int or float.
    :return: The converted time in seconds.
    :raise ValueError: A ValueError occurs when the type of the parameter is valid,
        but the format can't be recognized by this program.
    :raise TypeError: A TypeError occurs when the variable type of the parameter is none of NaN, int, float or string.
    """
    if pd.isna(time):
        return np.nan
    # 需要按秒、分、时的顺序提取出时间并转为整型，但是源文件中有两种时间格式:
    # 第一种是冒号分隔（大多数）
    # 第二种是单双引号分隔（少数，如部分TTT中）
    elif is_number(time):
        return float(time)
    elif type(time) == str:
        time = time.strip().lstrip("+'")
        # 对应第一种情况，包括表示与第一名的时间差和不含冒号的情况（纯数字时间）
        if ':' in time or is_number(time):
            time_extract = [float(i) for i in time.strip().split(":")[-1::-1]]
            time_sec = sum([x * y for (x, y) in zip(time_extract, [1, 60, 3600])])
            return time_sec
        # 对应第二种情况
        elif '"' in time or "'" in time:
            time_extract = [float(i) for i in re.split('[\'"]', time.strip())[-1::-1]]
            time_sec = sum([x * y for (x, y) in zip(time_extract, [1/100, 1, 60])])
            return time_sec
        elif len(time) == 0:
            return np.nan
        else:
            raise ValueError('Time format unsupported.')
    else:
        raise TypeError('Invalid time type.')


def write_csv_bom(dataframe, path, index=False, encoding=ENCODING):
    """
    To write .csv file with the BOM header.
    Receives only pandas.core.frame.DataFrame object as the data.
    """
    if encoding == 'utf-8':
        bom_bytes = codecs.BOM_UTF8
    else:
        bom_bytes = b''
    if not os.path.exists(os.path.split(path)[0]):
        os.makedirs(os.path.split(path)[0])
    with open(path, 'wb') as fw:
        fw.write(bom_bytes)
        fw.close()
    dataframe.to_csv(path, mode='a', index=index, encoding=encoding)
    return
