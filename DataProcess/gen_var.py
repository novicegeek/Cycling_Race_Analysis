# -*- coding: utf-8 -*-
"""Tidy data files, extracting information from single files, and generate variables for clustering."""


import os
import csv
import codecs
import pandas as pd
import re
import numpy as np
import log
import main
ENCODING = main.ENCODING


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


def isnumber(s):
    """
    To determine whether a variable is a discernable "number" to human.

    :param s: E.g., inputting '123' or 123 will get you True, while inputting '1+2+3' will get you False.
    :return: Boolean value.
    :raise ValueError: This error occurs when the input can not be interpreted as a number in any sense.
    """
    try:
        if pd.isna(s):
            return False
        float(s)
        return True
    except ValueError:
        return False


def time2sec(time):
    """Transform an input time to a number indicating the corresponding second counts.

    :param time: The time to be converted. Can be a string, int or float.
    :return: The converted time in seconds.
    :raise ValueError: A ValueError occurs when the type of the parameter is valid, 
        but the format can't be recognized by this program.
    :raise TypeError: A TypeError occurs when the variable type of the parameter is none of NaN, int, float or string.
    """
    if pd.isna(time):
        return
    # 需要按秒、分、时的顺序提取出时间并转为整型，但是源文件中有两种时间格式:
    # 第一种是冒号分隔（大多数）
    # 第二种是单双引号分隔（如TTT中，时长<1h）
    elif isnumber(time):
        return float(time)
    elif type(time) == str:
        time = time.strip().lstrip("+'")
        # 对应第一种情况，包括表示与第一名的追加时间、不含冒号的情况（纯数字时间）
        if ':' in time or isnumber(time):
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


# %%
class DataTidier(object):
    """用于数据文件的整理."""

    def __init__(self, root):
        self.root = root
        self.point_dict = {}
        return

    def tidy_all(self, types=('SC', 'GC', 'SGC')):
        """
        Adapter method for tidying all data files.

        This means to fill missing demographic information (e.g., team, country), 
        calculate primary derived race statistics (e.g., normalized ranking, 
        normalized time lag relative to the winner), and add some additional fields (e.g., full name, race/stage info)
        for every cyclists in the list.

        # Warning: This method functions IN-PLACE, which means the tidied file will cover the original copied, 
        none-tidied file in the same directory.

        :param types: By default, only the data files of Stage Classification, General Classification
            or Stage General Classification will be tidied.
        :return: The root FULL path storing the tided data files.
        """
        copy_source_dir, tidy_source_dir = self.file_copy_all()
        tidy_root = os.path.join(self.root, tidy_source_dir)

        # 对所有文件执行tidy
        file_list = get_file_list(tidy_root, extension='.csv')
        path_tidy_log = os.path.join(tidy_root, 'tidy_log.txt')
        tidy_log = log.auto_read_log(path_tidy_log)

        try:
            for file in file_list:
                file_name = os.path.split(file)[1]
                result_type = re.split('_', file_name)[3]
                if result_type in types and tidy_log[file_name] == 'N':
                    self.csv_tidy(file)
                    tidy_log[file_name] = 'Y'
        finally:
            log.auto_write_log(tidy_log, path_tidy_log)

        # 将已经写入dict的积分信息写入对应的文件（待完善）
        # for race in self.point_dict.keys():
        #     for year in self.point_dict[race].keys():
        #         for stage in self.point_dict[race][year].keys():
        #             self.write_pointdict(race, year, stage)
        return tidy_root

    def file_copy_all(self):
        """
        Copy all NOT-COPIED .csv files for further processing.

        :return: The source directory and targeted copy DIRECTORY NAME (not full path).
        """
        print('Please input the directory containing all source data files '
              '(directory name only or the whole path). \nTo use the default directory, press Enter.')
        source_dir = input()
        print('Please input the directory intended to contain all the copied files '
              '(directory name only or the whole path). \nTo use the default directory, press Enter.')
        copy_dir = input()
        if not source_dir:
            source_dir = 'Converted_Raw'
        else:
            source_dir = os.path.split(source_dir)[1]
        if not copy_dir:
            copy_dir = 'Converted_Tidied'
        else:
            copy_dir = os.path.split(copy_dir)[1]

        path_copy_log = os.path.join(self.root, source_dir, 'copy_log.txt')
        path_tidy_log = os.path.join(self.root, copy_dir, 'tidy_log.txt')
        copy_log = log.auto_read_log(path_copy_log)
        tidy_log = log.auto_read_log(path_tidy_log)

        file_list = get_file_list(os.path.join(self.root, source_dir), extension='.csv')
        try:
            for file in file_list:
                file_name_copy = os.path.split(file)[1]
                if file_name_copy in copy_log.keys() and copy_log[file_name_copy] == 'N':
                    self.file_copy(file, source_dir, copy_dir)
                    copy_log[file_name_copy] = 'Y'
                    tidy_log[file_name_copy] = 'N'
        finally:
            log.auto_write_log(copy_log, path_copy_log)
            log.auto_write_log(tidy_log, path_tidy_log)
        return source_dir, copy_dir

    @staticmethod
    def file_copy(file, source_dir=None, copy_dir=None):
        """
        To copy a single .csv data file.

        The files will be copied to a "counterpart" file directory, which means that the path strings of the copied
        and original file differ only in one directory level, while the other parts (including the file name) remain
        identical.

        :param file: The FULL path of the file to be copied.
        :param source_dir: Denotes the directory name at the level at which the copy path differs from the source path.
        :param copy_dir:
        :return: The FULL path of new file copy.
        """
        if not source_dir:
            source_dir = 'Converted_Raw'
        if not copy_dir:
            copy_dir = 'Converted_Tidied'

        pattern_path_str = '(.*?)' + source_dir + '(.*)'
        pattern_path = re.compile(pattern_path_str, re.S)
        copy_path = pattern_path.findall(file)[0][0] + copy_dir + pattern_path.findall(file)[0][1]

        # 注意codecs.open函数只能在目录存在的情况下创建新的文件，如果目录不存在就会报错，需要先生成目录
        if not os.path.exists(os.path.split(copy_path)[0]):
            os.makedirs(os.path.split(copy_path)[0])
        with open(file, encoding=ENCODING) as fr:
            rfile = csv.reader(fr)  # 生成generator，逐行遍历
            with codecs.open(copy_path, 'w', encoding=ENCODING) as fw:
                write = csv.writer(fw)
                for row in rfile:
                    write.writerow(row)
        return copy_path

    # 积分写入功能暂时未启用，代码不完善
    def add_pointdict(self, race, year, stage, point_scale):
        """
        将特定年份、特定比赛的UCI积分规则写入；只支持传入单一赛事、单一年份、单一赛段;
        只实现计时排名积分奖励的写入，爬坡积分、冲刺积分榜的积分奖励暂定手动写入

        :param point_scale: list, 若需要添加多赛事/多年份需要额外写循环
        :param race, year, stage: 包含赛事、年份以及赛段序号
        """

        # 先判断是否已在字典中，若已在则跳过添加
        if race not in self.point_dict.keys() or year not in self.point_dict[race].keys() \
                or stage not in self.point_dict[race][year].keys():
            self.point_dict[race] = {year: {stage: point_scale}}
        return

    def write_pointdict(self, race, year, stage):
        # 规定stage用缩写S+数字（赛段）或FC（Final Classification，总成绩）表示
        if not self.copy:  # 先检查是否已进行拷贝操作
            print('Please execute self.filecopy_all() first to avoid direct processing of source files.')
            return
        try:
            current_pointscale = self.point_dict[race][year][stage]
            current_dir = os.path.join(self.root, race, year)
            if stage == 'FC':
                stage_abbr = 'FC_GC'
            else:
                stage_abbr = stage + '_SC'
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if stage_abbr in file:
                        fread = pd.read_csv(file)
                        newdata = pd.DataFrame({'BIB': fread['BIB'], 'Points': current_pointscale})  # DataFrame可以实现按列插入
                        newfile = fread.merge(newdata, how='outer')
                        newfile.to_csv(file, mode='w', index=False, encoding=ENCODING)
        except KeyError:
            print('The point scale information has not been added.')
        return

    def csv_tidy(self, file, drop_list=('Phase', 'Heat')):
        """
        The core tidying method.

        This method tidies a single .csv file and is called iteratively by self.tidy_all() method.

        :param file: The COMPLETE path of the file to be tidied
        :param drop_list: The titles of columns to be removed from the dataframe
        """
        with open(file, 'r', encoding=ENCODING) as fr:  # Vuelta a España的ñ在路径中时用pd.read_csv()无法直接读取（编码问题），
            fread = pd.read_csv(fr)                     # 会导致无法读取文档，但是内建的open函数可以
            fr.close()
        print("Tidying {} ...".format(os.path.split(file)[1]))

        # To remove columns specified by parameter "drop_list"
        header_list = list(fread.columns)
        drop_list_copy = list(drop_list)
        for item in drop_list:
            if item not in header_list:  # If this column has been removed, delete the title from the candidate list
                drop_list_copy.remove(item)
        fread.drop(drop_list_copy, axis='columns', inplace=True)

        new_data_dict = {}

        # To combine the first name and last name
        if 'Full_Name' not in header_list:
            last_names = list(fread['Last Name'])
            first_names = list(fread['First Name'])
            full_names = [' '.join([first_name, last_name]) for (first_name, last_name) in zip(first_names, last_names)]
            new_data_dict['Full_Name'] = full_names

        # To get the actual number of participating cyclists (number of starters of the current competition)
        # And to add date information to records of non-finishers
        n_starters = len(fread['Age'])

        # 检查是否每一行都填写了排名和队伍数据，按排名遍历
        # 注意pandas读取时已经自动识别表头，所以数据的第一行行号是0不是1
        for rank in range(n_starters):
            if rank > 0 and pd.isna(fread['Rank'][rank]):  # 说明这个选手可能是和上一名选手同名次；注意NaN的布尔值是True
                if fread['IRM'][rank] != 'DNF' and fread['IRM'][rank] != 'DNS':  # 但是还需要判断是否完赛
                    fread.loc.__setitem__((rank, 'Rank'), fread['Rank'][rank-1])
                    if pd.isna(fread['Team'][rank]):
                        fread.loc.__setitem__((rank, 'Team'), fread['Team'][rank-1])
                """ 这里还需要确认，在TTT中没有完赛的车手在原始导出结果中有没有车队信息 """

        # 计算相对排名
        if 'Rank_Norm' not in header_list:
            if not pd.isna(fread['Rank'][0]):
                n_finishers = int(max(fread['Rank']))
                # 需要排查是否还存在其他未完赛的标记
                rank_norm_finishers = fread['Rank'] / n_finishers  # nan除以实数结果还是nan，不会报错
            else:
                rank_norm_finishers = fread['Rank']
            new_data_dict['Rank_Norm'] = rank_norm_finishers

        # 计算相对完成时差
        if 'Time_lag_Norm' in header_list:
            fread.rename(columns={'Time_lag_Norm': 'Time_Lag_Norm'}, inplace=True)
        elif 'Time_Lag_Norm' not in header_list:
            time_winner = fread['Result'][0]
            time_winner_sec = time2sec(time_winner)
            if not time_winner_sec:  # 如果无人完赛，则time2sec返回none；只要有人完赛，返回值布尔值即为True
                lags_norm = fread['Result']
            else:
                lags = fread['Result'][1:]
                lags_sec = [0]
                for lag in lags:
                    if not pd.isna(lag) and '+' in str(lag):       # 结果中有“+”号，直接判定是完成时差
                        lag_sec = time2sec(lag)
                    elif not pd.isna(lag):                    # 结果中无”+“号，需要分情况讨论
                        lag = str(lag).strip()
                        if time2sec(lag) >= time_winner_sec:  # 对应比赛结果为完成时间的情况
                            lag_sec = time2sec(lag) - time_winner_sec
                        else:                                 # 对应比赛结果为完成时差的情况
                            lag_sec = time2sec(lag)
                    else:
                        lag_sec = lag                         # 对应DNF或者DNS，成绩为nan类型，直接复制
                    lags_sec.append(lag_sec)
                lags_norm = [lag / time_winner_sec * 100 for lag in lags_sec]
            new_data_dict['Time_Lag_Norm'] = lags_norm

        # 提取比赛信息，加入到数据当中
        info_headers = ['Date', 'Race', 'Stage', 'Result_Type', 'Stage_Type']
        for header in info_headers:
            if header not in header_list:
                info = self.game_info(file)
                info_lists = [[item]*n_starters for item in info]
                new_data_dict.update([(info_header, info_list)
                                      for info_header, info_list in zip(info_headers, info_lists)])
                break

        # 把所有数据合并成dataframe并写入文件, 要求每一列的长度相同
        new_file = pd.DataFrame(dict(dict(fread), **new_data_dict))
        new_file.to_csv(file, mode='w', index=False, encoding=ENCODING)

        return

    @staticmethod
    def game_info(file):
        """
        To extract game information from file name or file path.

        :param file: May be the COMPLETE PATH or NAME of the file.
        :return: List of information embedded in the file name.
        """
        # pattern = re.compile('([0-9]{8})_([A-Z]+?)_([A-Z0-9]+?)_.*?', re.S)
        info = re.split('[_.]', os.path.split(file)[1])
        date, race, stage, result_type, stage_type = [info[0], info[1], info[2], info[3], info[4]]
        return [date, race, stage, result_type, stage_type]


# %%
class DataExtracter(object):
    """用于从原始数据提取出特定的变量，集中到统一的文件中用于聚类."""

    def __init__(self, root):
        self.root = root
        self.save_root = '/'.join([root, 'Converted_Extracted'])
        if not os.path.exists(self.save_root):
            os.makedirs(self.save_root)
        return

    def extract_all(self, race_range='Grand Tour', year_range=None, types=('SC', 'SGC', 'GC')):
        """The adapter method for batch extracting information from data files.

        By default, only the Grand Tours and Stage Classfication, Stage General Classification
        and General Classification will be extracted.
        """
        tidy_root = '/'.join([self.root, 'Converted_Tidied'])
        path_tidy_log = os.path.join(tidy_root, 'tidy_log.txt')
        tidy_log = log.auto_read_log(path_tidy_log)
        path_extract_log = '/'.join([self.save_root, 'extract_log.txt'])
        extract_log = log.auto_read_log(path_extract_log)

        if race_range == 'Grand Tour':
            race_range = ['Tour de France', "Giro d'Italia", 'Vuelta a España']
        elif type(race_range) == str:
            race_range = [race_range]

        try:
            for race in race_range:
                if not year_range:
                    # extract all years
                    race_dir = '/'.join([tidy_root, race])
                    for item in os.listdir(race_dir):
                        if os.path.isdir('/'.join([race_dir, item])):
                            extract_log = self.extract(tidy_root, race, item, types, tidy_log, extract_log)
                            log.auto_write_log(extract_log, path_extract_log)
                else:
                    # extract only specified years
                    for year in year_range:
                        extract_log = self.extract(tidy_root, race, year, types, tidy_log, extract_log)
                        log.auto_write_log(extract_log, path_extract_log)
        finally:
            log.auto_write_log(extract_log, path_extract_log)
        return

    def extract(self, root, race, year, types, tidy_log, extract_log):
        """Extract information for a single race and year.
        
        return: Extract log.
        """
        year = str(year)
        save_dir = '/'.join([self.save_root, race])
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file_name = '_'.join([race, year, 'Extracts.csv'])

        if save_file_name not in extract_log.keys() or \
                extract_log[save_file_name] == 'N':
            source_file_dir = os.path.join(root, race, year)
            file_list = get_file_list(source_file_dir, extension='.csv')
            start_list = 'N'
            for file in file_list:
                file_name = os.path.split(file)[1]
                stage, result_type, race_type = os.path.splitext(file_name)[0].split('_')[2:]
                if result_type in types and tidy_log[file_name] == 'Y':
                    print("- Extracting information from {}...".format(file_name))
                    with open(file, 'r', encoding=ENCODING) as fr:
                        source_data = pd.read_csv(fr)
                        fr.close()
                    if start_list == 'N':
                        # create cyclists start list and extract the demographic information
                        # Including: Full name, nationality, team, gender, and age
                        print("-- Creating start list for {} {}...".format(race, year))
                        extract_df = self.create_start_list(source_data)
                        start_list = 'Y'
                    extract_df = self.add_extract_info(source_data, extract_df,
                                                       stage_info=[stage, result_type, race_type])
            extract_df.to_csv('/'.join([save_dir, save_file_name]), index=False, encoding=ENCODING)
            extract_log[save_file_name] = 'Y'

        return extract_log

    @staticmethod
    def create_start_list(source_data, fields=('Full_Name', 'Country', 'Team', 'Gender', 'Age')):
        """Create start list and extract the cyclists' demographic information."""
        for field in fields:
            if 'start_list' not in dir():
                start_list = pd.DataFrame(source_data[field])
            else:
                start_list = start_list.join(source_data[field])
        return start_list

    @staticmethod
    def add_extract_info(source_data, extract_df, stage_info, extract_fields=('Rank', 'Rank_Norm', 'Time_Lag_Norm')):
        """Add information to the extract data file."""
        new_fields = {}
        for field in extract_fields:
            new_fields[field] = '_'.join(stage_info+[field])
        cyclists = extract_df['Full_Name']
        for row in source_data.iterrows():
            cyclist = row[1]['Full_Name']
            if len(cyclists[cyclists == cyclist].index) > 0:
                match_row = cyclists[cyclists == cyclist].index[0]  # To get the index of row of the cyclist
            else:
                match_row = 0
            for field in extract_fields:
                extract_df.loc.__setitem__((match_row, new_fields[field]), row[1][field])
        return extract_df


# %%
class VarGenerator(object):
    """从原始变量数据计算衍生变量，直接用于聚类模型."""

    def __init__(self, root='.'):
        self.root = root
        self.cluster_root = '/'.join([root, 'For_Clustering'])
        return

    def gen_vars_all(self, race_range='Grand Tour', year_range='all', var_list=None):
        """ To calculate variables used directly for clustering and write them into data files """
        var_list = self._gen_var_list(var_list)

        if race_range == 'Grand Tour':
            race_range = ['Tour de France', "Giro d'Italia", 'Vuelta a España']
        elif type(race_range) == str:
            race_range = [race_range]

        for race in race_range:
            file_dir = '/'.join([self.cluster_root, race])
            file_list = get_file_list(file_dir, extension='.csv')
            if year_range == 'all':
                for file in file_list:
                    file_year = os.path.split(file)[1].split('_')[1]
                    print("----Generating variables for {} {}...----".format(race, file_year))
                    self.gen_vars(file, var_list)
            else:
                if type(year_range) == str or type(year_range) == int:
                    year_range = [year_range]
                for file in file_list:
                    file_year = os.path.split(file)[1].split('_')[1]
                    if file_year in year_range or int(file_year) in year_range:
                        print("----Generating variables for {} {}...----".format(race, file_year))
                        self.gen_vars(file, var_list)
        return

    def gen_vars(self, source_path, var_list):
        with open(source_path, 'r', encoding=ENCODING) as fr:
            source_data = pd.read_csv(fr)
            fr.close()
        gen_data = source_data
        for var in var_list:
            if var[0] != 'S' and var[0] != 'F':
                continue
            elif 'stage_list' not in dir():
                stage_list = None
            if 'SC_rank_abs' in var or var == 'stages_finished':
                gen_data, stage_list = self._gen_single_var(gen_data, var, stage_list)
            else:
                gen_data = self._gen_single_var(gen_data, var)[0]
        gen_data.to_csv(source_path, index=False)  # pd.read_csv()不能读带有特殊字符的路径，但是df.to_csv()可以正常写
        return

    @staticmethod
    def _gen_single_var(source_data, var, stage_list=None):
        """
        :param source_data:
        :param var:
        :param stage_list: When calculating Stage Classification Ranking (abs)-related variables,
                           stage list can be imported
        :return: The dataframe with variables added and stage list (if applicable)
        """
        cols = source_data.columns
        if not stage_list or len(stage_list) == 0:
            stage_list = []

        if var == 'stages_finished':
            if not stage_list:
                for col in cols:
                    if 'S' in col.split('_')[0] and 'SC' in col and 'Rank' in col and 'Norm' not in col:
                        stage_list.append(col)
            for row in source_data.iterrows():
                count = 0
                for stage in stage_list:
                    if isnumber(row[1][stage]):
                        count += 1
                source_data.loc.__setitem__((row[0], var), count)
        elif var == 'GC_rank_abs':
            for row in source_data.iterrows():
                source_data.loc.__setitem__((row[0], var), row[1]['FC_GC_IRR_Rank'])
        elif 'SC_rank_abs' in var:
            if not stage_list:
                for col in cols:
                    if 'S' in col.split('_')[0] and 'SC' in col and 'Rank' in col and 'Norm' not in col:
                        stage_list.append(col)
            for row in source_data.iterrows():
                temp_list = []
                if 'all' in var:
                    for stage in stage_list:
                        if isnumber(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'IRR' in var:
                    for stage in stage_list:
                        if 'TT' not in stage and isnumber(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'TT' in var:
                    for stage in stage_list:
                        if 'TT' in stage and isnumber(row[1][stage]):
                            temp_list.append(row[1][stage])
                if len(temp_list) > 0:
                    if 'mean' in var:
                        source_data.loc.__setitem__((row[0], var), sum(temp_list)/len(temp_list))
                    elif 'max' in var:
                        source_data.loc.__setitem__((row[0], var), min(temp_list))
                    elif 'SD' in var:
                        source_data.loc.__setitem__((row[0], var), np.std(temp_list))
                else:
                    source_data.loc.__setitem__((row[0], var), np.nan)
        elif 'max_SGC' in var:
            if var == 'GC-max_SGC' and 'stage_max_SGC' in cols:  # 如果最大单站总排名已经算过，就不用再算一遍了
                for row in source_data.iterrows():
                    if isnumber(row[1]['stage_max_SGC']):
                        source_data.loc.__setitem__((row[0], var), row[1]['FC_GC_IRR_Rank'] - row[1]['stage_max_SGC'])
            else:
                if not stage_list:
                    for col in cols:
                        if 'SGC' in col and 'Rank' in col and 'Norm' not in col:
                            stage_list.append(col)
                for row in source_data.iterrows():
                    max_list = [999, 0]  # 前面的表示最高SGC，后面的表示对应的赛段；注意高排名对应低数值
                    for stage in stage_list:
                        if isnumber(row[1][stage]) and row[1][stage] < max_list[0]:
                            max_list[0] = row[1][stage]
                            max_list[1] = int(stage.split('_')[0].split('S')[1])
                    if var == 'stage_max_SGC':
                        source_data.loc.__setitem__((row[0], var), max_list[0])
                    else:
                        source_data.loc.__setitem__((row[0], var), row[1]['FC_GC_IRR_Rank'] - max_list[0])
        elif 'SC_time_lag_norm' in var:
            if not stage_list:
                for col in cols:
                    if 'S' in col.split('_')[0] and 'SC' in col and 'Time_Lag' in col:
                        stage_list.append(col)
            for row in source_data.iterrows():
                temp_list = []
                if 'all' in var:
                    for stage in stage_list:
                        if isnumber(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'IRR' in var:
                    for stage in stage_list:
                        if 'TT' not in stage and isnumber(row[1][stage]):
                            temp_list.append(row[1][stage])
                if len(temp_list) > 0:
                    if 'mean' in var:
                        source_data.loc.__setitem__((row[0], var), sum(temp_list)/len(temp_list))
                else:
                    source_data.loc.__setitem__((row[0], var), np.nan)
        else:   # If none of the case matches, then leave the data unchanged
            pass
        return source_data, stage_list

    @staticmethod
    def _gen_var_list(option='lite'):
        """
        Generate list for variables to be calculated
        :param option: Can be 'full'(explicit list), 'lite' or None(short list), or a list of name of variables
        """
        if option == 'full':
            var_list = [
                'stages_finished',
                'mean_SC_rank_abs_all', 'mean_SC_rank_abs_TT', 'mean_SC_rank_abs_IRR',
                'mean_SC_rank_norm_all', 'mean_SC_rank_norm_TT', 'mean_SC_rank_norm_IRR',
                'mean_SC_time_lag_norm_all', 'mean_SC_time_lag_norm_TT', 'mean_SC_time_lag_norm_IRR',
            ]
        elif option == 'lite' or not option:
            var_list = [
                'stages_finished', 'GC_rank_abs',                           # 完成的赛段数，最终总排名
                'mean_SC_rank_abs_all', 'mean_SC_rank_abs_IRR',             # 平均单站排名
                'max_SC_rank_abs_all', 'max_SC_rank_abs_IRR',               # 最高单站排名
                'SD_SC_rank_abs_all', 'SD_SC_rank_abs_IRR',                 # 单站排名标准差
                'stage_max_SGC', 'GC-max_SGC',                              # 第一次取得最高总排时的赛段，全程最高总排和最终总排差
                'mean_SC_time_lag_norm_all', 'mean_SC_time_lag_norm_IRR',   # 与赛段冠军的完赛时差百分比均值
            ]
        elif type(option) == list:
            var_list = option
        else:
            var_list = None
        return var_list
