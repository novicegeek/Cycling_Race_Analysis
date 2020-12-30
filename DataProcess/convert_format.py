# -*- coding: utf-8 -*-
"""Convert files to a different format."""


import os
import codecs
import csv
import xlrd
import log
import gen_var
import global_vars
import re
ENCODING = global_vars.get_value('ENCODING')


def xlsx2csv(file, path_result=None):
    """
    Convert .xlsx document to a .csv one.

    :param file: The source file path to be converted.
    :param path_result: The path of converted file; by default, the converted file
        will be saved in the same directory as the source file.
    :return: The COMPLETE path of converted file.
    """
    if not file:  # 若文件名为空则直接返回
        return

    if path_result:
        new_filepath = os.path.splitext(path_result)[0] + '.csv'  # 更改扩展名为.csv
    else:
        new_filepath = os.path.splitext(file)[0] + '.csv'  # 如果没有指定目标路径，则默认和原文件放在同一目录下

    if not os.path.exists(os.path.split(new_filepath)[0]):
        os.makedirs(os.path.split(new_filepath)[0])
    with codecs.open(new_filepath, 'w', encoding=ENCODING) as f:  # 这里不加encoding会报错，默认解码方式不是utf-8
        write = csv.writer(f)
        workbook = xlrd.open_workbook(file)
        table = workbook.sheet_by_index(0)
        # result_col_index = table.row_values(0).index('Result')  # 找到存储比赛时间的列序号
        for row in range(table.nrows):
            row_value = table.row_values(row)
            # if row > 1 and '+' not in row_value[result_col_index]:  # 这一步是为了转换之后所有非冠军运动员成绩前都保留+号
            #     row_value[result_col_index] = '+' + str(row_value[result_col_index])
            write.writerow(row_value)
        f.close()
    return new_filepath


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
        source_dir = self.root + '/Raw'
        convert_dir = self.root + '/Converted_Raw'
        path_convert_log = os.path.join(source_dir, 'convert_log.txt')
        path_copy_log = os.path.join(convert_dir, 'copy_log.txt')
        convert_log = log.auto_read_log(path_convert_log)
        copy_log = log.auto_read_log(path_copy_log)

        if not race_range:
            race_range = []
            for race_dir in os.listdir(source_dir):
                if os.path.isdir(os.path.join(source_dir, race_dir)):
                    race_range.append(race_dir)
        race_dirs = [os.path.join(source_dir, race_dir) for race_dir in race_range]
        file_list = []
        if not year_range:
            for race_dir in race_dirs:
                file_list += gen_var.get_file_list(race_dir, extension='.xlsx')
        else:
            for race_dir in race_dirs:
                for year in year_range:
                    year_dir = race_dir + '/' + year
                    file_list += gen_var.get_file_list(year_dir, extension='.xlsx')

        pattern_source_path = re.compile(source_dir+'(.*)', re.S)
        try:
            for file in file_list:
                file_name_convert = os.path.split(file)[1]
                if file_name_convert not in convert_log.keys() \
                        or convert_log[file_name_convert] == 'N':
                    result_path_xlsx = convert_dir + pattern_source_path.findall(file)[0]
                    file_name_copy = os.path.split(xlsx2csv(file, path_result=result_path_xlsx))[1]
                    convert_log[file_name_convert] = 'Y'
                    copy_log[file_name_copy] = 'N'
        finally:
            log.auto_write_log(convert_log, path_convert_log)
            log.auto_write_log(copy_log, path_copy_log)
        return
