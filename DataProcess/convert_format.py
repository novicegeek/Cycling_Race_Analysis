# -*- coding: utf-8 -*-
"""Convert files to a different format."""


import os
import pandas as pd
import basics
import global_vars
import log


ENCODING = global_vars.get_value('ENCODING')


class FormatConverter(object):
    """For file format conversion. Currently only conversion from .xlsx to .csv is supported."""

    def __init__(self, root):
        """
        :param root: Set the root directory in which the conversion will be performed.
        """
        self.root = root
        return

    def convert_xlsx2csv(self, race_range=None, year_range=None):
        """
        Convert .xlsx raw data files into .csv ones.

        :param race_range: Can be a LIST of race names the file of which will be converted;
            by default, ALL files will be converted.
        :param year_range: The same rule as above.
        """
        source_dir = self.root + r'\Raw'
        convert_dir = self.root + r'\Converted_Raw'

        path_convert_log = os.path.join(source_dir, 'convert_log.txt')
        convert_log = log.auto_read_log(path_convert_log)
        path_tidy_log = os.path.join(convert_dir, 'tidy_log.txt')
        tidy_log = log.auto_read_log(path_tidy_log)

        if not race_range:
            race_range = []
            for race_dir in os.listdir(source_dir):
                if os.path.isdir(os.path.join(source_dir, race_dir)):
                    race_range.append(race_dir)
        race_dirs = [os.path.join(source_dir, race_dir) for race_dir in race_range]
        file_list = []
        if not year_range:
            for race_dir in race_dirs:
                file_list += basics.get_file_list(race_dir, extension='.xlsx')
        else:
            for race_dir in race_dirs:
                for year in year_range:
                    year_dir = os.path.join(race_dir, year)
                    file_list += basics.get_file_list(year_dir, extension='.xlsx')

        try:
            for file in file_list:
                file_name_convert = os.path.split(file)[1]
                if file_name_convert not in convert_log.keys() \
                        or convert_log[file_name_convert] == 'N':
                    result_path_xlsx = file.replace('Raw', 'Converted_Raw')
                    self.xlsx2csv(file, converted_file_path=result_path_xlsx)
                    convert_log[file_name_convert] = 'Y'
                    tidy_log[file_name_convert] = 'N'
        finally:
            log.auto_write_log(convert_log, path_convert_log)
            log.auto_write_log(tidy_log, path_tidy_log)
        return convert_dir

    @staticmethod
    def xlsx2csv(raw_file_path, converted_file_path=None):
        """
        Convert .xlsx document to a .csv one.

        :param raw_file_path: The source file path to be converted.
        :param converted_file_path: The path of converted file; by default, the converted file
            will be saved in the same directory as the source file.
        :return: The COMPLETE path of converted file.
        """
        if not raw_file_path:  # 若源文件名为空则直接返回
            return

        print('---------- Converting {} ----------'.format(os.path.split(raw_file_path)[1]))
        if converted_file_path:
            new_file_path = os.path.splitext(converted_file_path)[0] + '.csv'  # 确保扩展名为.csv
        else:
            new_file_path = os.path.splitext(raw_file_path)[0] + '.csv'  # 如果没有指定目标路径，则默认和原文件放在同一目录下

        if not os.path.exists(os.path.split(new_file_path)[0]):
            os.makedirs(os.path.split(new_file_path)[0])

        # Excel打开.csv文件时会先读取BOM文件头，但是程序调用的库不一定遵循这一套标准，可能会不写BOM文件头，
        # 造成用Excel打开乱码（程序读取仍正常），影响查看，所以要先手动写入一个BOM文件头
        # 先读取成dataframe，然后再往csv里追加写入正文内容
        basics.write_csv_bom(pd.read_excel(raw_file_path, encoding=ENCODING), new_file_path)
        return new_file_path
