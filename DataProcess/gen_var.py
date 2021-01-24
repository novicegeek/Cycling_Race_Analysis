# -*- coding: utf-8 -*-
"""Tidy data files, extracting information from single files, and generate variables for clustering."""


import os
import re
import numpy as np
import pandas as pd
import basics
import cyclists_list
import global_vars
import log


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


# %%
class DataTidier(object):
    """用于数据文件的整理."""

    def __init__(self, root=None):
        self.root = ROOT if not root else root
        self.point_dict = {}
        return

    def tidy_all(self, races, seasons,
                 types=('SC', 'GC', 'SGC'), ignore_log=False, include_ttt=False, **kwargs):
        """
        Adapter method for tidying all data files.

        This means to fill missing demographic information (e.g., team, country), 
        calculate primary derived race statistics (e.g., normalized ranking, 
        normalized time lag relative to the winner), and add some additional fields (e.g., full name, race/stage info)
        for every cyclists in the list.

        # Warning: This method operates IN-PLACE, which means the tidied file will cover the original copied,
        none-tidied file in the same directory.

        :param races:
        :param seasons:
        :param types: By default, only the data files of Stage Classification, General Classification
            or Stage General Classification will be tidied.
        :param ignore_log: Boolean. If True, the file will be converted regardless of its record in the log.
        :param include_ttt: Boolean.
        :return: The root FULL path storing the tided data files.
        """
        source_dir = os.path.join(self.root, 'Converted_Raw')
        tidy_dir = os.path.join(self.root, 'Converted_Tidied')

        path_tidy_log = os.path.join(source_dir, 'tidy_log.txt')
        tidy_log = log.auto_read_log(path_tidy_log)
        path_tidy_warning_log = os.path.join(source_dir, 'tidy_warning_log.txt')
        fw_warning = open(path_tidy_warning_log, 'w', encoding=ENCODING)

        races_list_path = os.path.join(self.root, r"MetaData\races_list.csv")
        with open(races_list_path, 'r', encoding=ENCODING) as fr:
            races_list = pd.read_csv(fr)
            fr.close()
        races_dict = dict([(row[1]['ID'], row[0]) for row in races_list.iterrows()])

        cyc_list_path = os.path.join(self.root, r"MetaData\cyclists_list.csv")
        with open(cyc_list_path, 'r', encoding=ENCODING) as fr:
            cyc_list = pd.read_csv(fr)
            fr.close()
        cyclists_dict = dict([
                ('@'.join(list(row[1][['Full Name', 'Country']])), row[1]['ID']) for row in cyc_list.iterrows()
        ])  # Hash cur_list to accelerate matching. Dict structure: {Full Name@Country: ID}.

        races = basics.get_races_list(races)
        seasons = basics.get_seasons_list(seasons)
        last_write = 0

        for race in races:
            for season in seasons:
                cur_dir = os.path.join(source_dir, race, season)
                for file_name in os.listdir(cur_dir):
                    file_path = os.path.join(cur_dir, file_name)
                    stage, result_type, stage_type = re.split('[._]', file_name)[2:5]
                    if stage == 'FC' and result_type == 'SC':  # 注意FC情况的判断比较特殊，要考虑FC_SC这种混淆情况
                        continue
                    elif not include_ttt and stage_type == 'TTT':
                        continue
                    elif result_type in types and \
                            (ignore_log or file_name not in tidy_log.keys() or tidy_log[file_name] == 'N'):
                        copy_file_path = self.file_copy(file_path)
                        is_multi_stage = True if race in global_vars.get_value('MULTI-STAGES') else False
                        # Only operates on copy of the raw file
                        new_file_name, fw_warning = self.csv_tidy(
                            copy_file_path, cyclists_dict, races_list, races_dict, is_multi_stage, fw_warning, **kwargs
                        )
                        if new_file_name is not None:
                            tidy_log[file_name] = new_file_name  # 因为文件名可能更改，为了找到对应就把value设置成新的文件名
                            last_write += 1
                        else:  # 返回None说明出错，需要跳过这一个文件，并且把已经复制的文件删除
                            os.remove(copy_file_path)
                            continue
                    if not last_write % 20:
                        log.auto_write_log(tidy_log, path_tidy_log)

        log.auto_write_log(tidy_log, path_tidy_log)
        fw_warning.close()

        return tidy_dir

    def csv_tidy(self, source_path, cyclists_dict, races_list, races_dict, is_multi_stage, fw_warning_log,
                 drop_list=('Phase', 'Heat'),
                 add_race_info=True, prior_check=True, rename=True, write_record_dict=True, **kwargs):
        """
        The core tidying method.

        This method tidies a single .csv file and is called iteratively by self.tidy_all() method.

        :param source_path: The COMPLETE path of the file to be tidied
        :param cyclists_dict: The dictionary generated from cyclists_list, storing the full names,
            countries and row indexes for fast matching. Structure: {Full Name@Country: ID}.
            See also in cyclists_list.py.
        :param races_list: The meta-data file of races.
        :param races_dict: Dictionary storing the race information.
        :param is_multi_stage: Boolean. Whether this is a multi-stage race.
        :param fw_warning_log: The TextIOWrapper of log for outputting warning information.
        :param drop_list: The titles of columns to be removed from the dataframe.
        :param add_race_info: Whether to add race information, including winner's average speed
            and median average speed to the existing races list.
        :param prior_check: Boolean (default True). Whether to perform data check before copying and calculating
            derivative variables. Setting this to False will accelerate the tidying, but may leave the data flawed.
        :param rename: Whether to rename the tidied file as race id_stage type_result type.csv (By default True).
            If False, the file name will remain the same as is copied, i.e. the 5-segment format.
        :param write_record_dict: Boolean. Whether to write the record into the .json file for this cyclist.
        """
        # Vuelta a España的ñ在路径中时用pd.read_csv()无法直接读取（编码问题），会导致无法读取文档，但是内建的open函数可以
        with open(source_path, 'r', encoding=ENCODING) as fr:
            raw_data = pd.read_csv(fr)
            fr.close()
        print("Tidying {} ...".format(os.path.split(source_path)[1]))
        fw_warning_log.write("Tidying {} ...\n".format(os.path.split(source_path)[1]))

        # 第一步先检查这整个文件是否有效
        time_winner = raw_data['Result'][0]
        time_winner_sec = basics.time2sec(time_winner)
        if pd.isna(time_winner_sec):  # 如果无人完赛或成绩为空字符串，则time2sec返回nan；如果成绩无法识别则会报错；否则会返回float
            fw_warning_log.write("    Warning: The winner's time is invalid.\n")
            return None, fw_warning_log

        # Prior check
        # 要避免的问题：
        # 1) IRM不为空（非正常完赛），但还有ranking和time成绩（ranking应该已经被手动清除，但以防万一；time全设为nan）
        #    ——如果是有ranking则print，否则将time写为nan
        # 2) IRM为空，且time为空，但还有ranking（应该也已经被扫描出来，即可能为OTL之类的情况，但以防万一）  ——print
        # 3) IRM为空，且ranking为空，但还有time（这种情况可能比较多，不用管）  ——将time写为nan
        # 4) 冠军成绩无效？--SC和GC文件都已经改过了，SGC还没改  ——暂时不处理SGC
        if prior_check:
            for row in raw_data.iterrows():
                if not pd.isna(row[1]['IRM']):
                    if not pd.isna(row[1]['Rank']):
                        fw_warning_log.write("    Cyclist {}: Both IRM and ranking exist\n".format(row[0]))
                        return None, fw_warning_log
                    elif not pd.isna(row[1]['Result']):
                        raw_data.loc.__setitem__((row[0], 'Result'), np.nan)
                else:
                    if not pd.isna(row[1]['Rank']) and pd.isna(row[1]['Result']):
                        fw_warning_log.write("    Cyclist {}: Ranking exists without time\n".format(row[0]))
                        return None, fw_warning_log
                    elif pd.isna(row[1]['Rank']) and not pd.isna(row[1]['Result']):
                        raw_data.loc.__setitem__((row[0], 'Result'), np.nan)

        # To remove columns specified by parameter "drop_list"
        header_list = list(raw_data.columns)
        drop_list_list = list(drop_list)
        for item in drop_list:
            if item not in header_list:  # If this column has been removed, no need to remove it again
                drop_list_list.remove(item)
        raw_data.drop(drop_list_list, axis='columns', inplace=True)

        # Starters include DNS, DNF, DSQ and OTL cyclists
        n_starters = len(raw_data)
        info = self.game_info(source_path, is_multi_stage)
        info_headers_dict = {'Race ID': 0, 'Date': 1, 'Race': 2, 'Stage': 3, 'Result Type': 4, 'Stage Type': 5}

        # 对于TTT：检查是否每一行都填写了排名和队伍数据，按行遍历
        stage_type = info[info_headers_dict['Stage Type']]
        if stage_type == 'TTT':
            for rank in range(n_starters):
                if rank > 0 and pd.isna(raw_data['Rank'][rank]):  # 说明这个选手可能是和上一名选手同名次；注意NaN的布尔值是True
                    if raw_data['IRM'][rank] not in ('DNF', 'DNS', 'DSQ', 'OTL'):  # 还需要判断是否为正常完赛
                        raw_data.loc.__setitem__((rank, 'Rank'), 0)    # 若完赛的车手出现排名数据缺失，则标记为0（表明信息缺失），不检查队伍情况
                """UCI上TTT的数据质量非常差，如果需要的话，考虑从赛事官网直接获取数据"""

        new_data_dict = {}
        # To combine the first name and last name
        if 'Full Name' not in header_list:
            last_names = list(raw_data['Last Name'])
            first_names = list(raw_data['First Name'])
            full_names = [' '.join([first_name, last_name]) for (first_name, last_name) in zip(first_names, last_names)]
            new_data_dict['Full Name'] = full_names
        else:
            full_names = raw_data['Full Name']

        # 加入车手ID，并且顺便把未正常完赛（无rank）的人的时间成绩清空
        ids_list = []
        order = 0
        for name in full_names:
            if pd.isna(raw_data['Rank'][order]) and pd.notna(raw_data['Result'][order]):
                raw_data.loc.__setitem__((order, 'Result'), np.nan)
            cyclist_id = np.nan
            try:
                country = raw_data['Country'][order]
                key = '@'.join([name, country])
                cyclist_id = cyclists_dict[key]
            except IndexError:  # raw_data的Country列比Full Name列短（有的车手缺失信息）
                fw_warning_log.write("    Warning: No country information for {}\n".format(name))
            except KeyError:  # cyclists_dict中找不到这名车手
                fw_warning_log.write("    Warning: Can't find {} in the cyclists list\n".format(name))
            finally:
                ids_list.append(cyclist_id)
                order += 1
        new_data_dict.update({'Cyclist ID': ids_list})

        # 计算相对排名（以名义完赛人数为基数）
        # 关于DSQ车手：虽然这部分人最终成绩被取消，但是他们的成绩会被用作排名
        # 比如一个DSQ的人排第100位然后成绩被取消，那么第100位的人就会空缺，不会向前候补
        # 为避免出现相对排名>1的情况，目前的排名计算是把DSQ的人也算在基数里
        if not pd.isna(raw_data['Rank'][0]):
            n_nominal_finishers = int(max(raw_data['Rank']))
            rank_norm_finishers = raw_data['Rank'] / n_nominal_finishers  # nan除以实数结果还是nan，不会报错
        else:
            rank_norm_finishers = raw_data['Rank']
        new_data_dict['Rank_Norm'] = rank_norm_finishers

        # Get the length of the current race for calculating speed
        race_id = info[info_headers_dict['Race ID']]
        row_index = races_dict.get(race_id)
        if row_index is None:
            race_length = np.nan
            fw_warning_log.write("    Warning: Race {} is not in the list.\n".format(race_id))
        else:
            race_length = float(races_list['Length'][row_index])

        # 计算总完成时间、相对完成时差、平均速度、与冠军的平均速度之比、与中位数平均速度之比
        lags = raw_data['Result'][1:]
        lags_sec = [0]
        for lag in lags:
            if not pd.isna(lag) and '+' in str(lag):  # 结果中有“+”号，直接判定是完成时差
                lag_sec = basics.time2sec(lag)
            elif not pd.isna(lag):  # 结果中无”+“号，需要分情况讨论，如果大于等于冠军时间则说明是完整时长
                lag_sec = basics.time2sec(str(lag))
                lag_sec = (lag_sec - time_winner_sec) if lag_sec >= time_winner_sec else lag_sec
            else:
                lag_sec = lag  # 对应DNF或者DNS，成绩为nan，直接复制。注意：有时OTL和DSQ的车手是有时间成绩的，只是没有排名成绩
            lags_sec.append(lag_sec)
        total_time_sec = [lag + time_winner_sec for lag in lags_sec]
        lags_norm = [lag / time_winner_sec * 100 for lag in lags_sec]
        avgs_kph = [race_length / ind_sec * 3600 for ind_sec in total_time_sec]
        avgs_rel_to_winner = [time_winner_sec / ind_sec for ind_sec in total_time_sec]
        # 计算中位数时不会自动跳过na，所以要取前面的有效成绩行
        n_valid_finishers = raw_data['Rank'].count()
        median_avg = np.median(avgs_kph[:n_valid_finishers])
        avgs_rel_to_median = [avg_kph / median_avg for avg_kph in avgs_kph]
        new_data_dict.update({
            'Total Time': total_time_sec,
            'Time Lag_Norm': lags_norm,
            'Avg Speed (kph)': avgs_kph,
            'Avg Speed Rel to Winner': avgs_rel_to_winner,
            'Avg Speed Rel to Median': avgs_rel_to_median
        })

        if add_race_info and row_index is not None:
            if (not races_list['Is Multi-Stage'][row_index]) \
                    or (races_list['Is A Stage'][row_index] and info[info_headers_dict['Result Type']] == 'SC') \
                    or info[info_headers_dict['Result Type']] == 'GC':
                races_list.loc.__setitem__((row_index, 'Starters'), n_starters)
                races_list.loc.__setitem__((row_index, 'Valid Finishers'), n_valid_finishers)
                races_list.loc.__setitem__((row_index, 'Finishing Rate'), n_valid_finishers / n_starters)
                races_list.loc.__setitem__((row_index, 'Winner Avg Speed'), avgs_kph[0])
                races_list.loc.__setitem__((row_index, 'Median Avg Speed'), median_avg)
                basics.write_csv_bom(races_list, os.path.join(self.root, r"MetaData\races_list.csv"))

        # 提取比赛信息，加入到数据当中
        # dict存储的是提取的全部信息，按照self.game_info返回的次序编号；list存储的是想要添加到文件中的信息
        target_info_headers_list = ['Race ID', 'Date', 'Stage Type', 'Result Type']
        for header in target_info_headers_list:
            if header not in header_list:  # 一旦发现缺一项，就全部重新添加
                info_lists = [[info[info_headers_dict[field]]]*n_starters for field in target_info_headers_list]
                new_data_dict.update([(info_header, info_list)
                                      for info_header, info_list in zip(target_info_headers_list, info_lists)])
                break

        # 把所有数据合并成dataframe并全部重写入文件, 要求每一列的长度相同
        new_data = pd.DataFrame(dict(dict(raw_data), **new_data_dict))
        basics.write_csv_bom(new_data, source_path)

        # 改变原有的命名方式
        if rename:
            new_file_name = '_'.join([
                race_id, info[info_headers_dict['Stage Type']], info[info_headers_dict['Result Type']]
            ]) + '.csv'
            new_file_path = os.path.join(os.path.split(source_path)[0], new_file_name)
            try:
                os.rename(source_path, new_file_path)
            except FileExistsError:
                os.remove(new_file_path)
                os.rename(source_path, new_file_path)
        else:
            new_file_name = os.path.split(source_path)[1]

        # 创建每个车手的.json文件
        if write_record_dict:
            create_records = cyclists_list.CreateCyclistRecords()
            for row in new_data.iterrows():
                create_records.add_record(row[1], result_type=info[info_headers_dict['Result Type']], **kwargs)

        return new_file_name, fw_warning_log

    @staticmethod
    def game_info(file, is_multi_stage):
        """
        To extract game information from file name or file path.

        :param file: May be the COMPLETE PATH or NAME of the file.
        :param is_multi_stage: Boolean.
        :return: List of information embedded in and created from the file name.
        """
        info = re.split('[_.]', os.path.split(file)[1])
        date, race, stage, result_type, stage_type = info[0:5]
        race_id = basics.create_race_id(race, date[:4], is_multi_stage,
                                        from_race_meta=False, stage=stage)
        return [race_id, date, race, stage, result_type, stage_type]

    @staticmethod
    def file_copy(source_path, source_dir=None, copy_dir=None):
        """
        To copy a single .csv data file.

        The files will be copied to a "counterpart" file directory, which means that the path strings of the copied
        and original file differ only in one directory level, while the other parts (including the file name) remain
        identical.

        :param source_path: The FULL path of the file to be copied.
        :param source_dir: Denotes the directory name at the level at which the copy path differs from the source path.
            By default "Converted_Raw".
        :param copy_dir: Similar to source_dir.
            By default "Converted_Tidied".
        :return: The FULL path of new file copy.
        """
        if not source_dir:
            source_dir = 'Converted_Raw'
        if not copy_dir:
            copy_dir = 'Converted_Tidied'

        pattern_path_str = '(.*?)' + source_dir + '(.*)'
        pattern_path = re.compile(pattern_path_str, re.S)
        copy_path = copy_dir.join([part for part in pattern_path.findall(source_path)[0]])

        if not os.path.exists(os.path.split(copy_path)[0]):
            os.makedirs(os.path.split(copy_path)[0])
        with open(source_path, 'rb') as fr:
            with open(copy_path, 'wb') as fw:
                fw.write(fr.read())
                fw.close()
            fr.close()
        return copy_path

    @staticmethod
    def _create_race_id(date, race_abbr, stage, align=2):
        """Create race ID from information extracted from file name."""
        if 'S' in stage:
            stage_number = stage.split('S')[1]
            stage = 'S' + '0' * (align - len(stage_number)) + stage_number
        elif stage == 'FC':
            stage = 'R01'
        elif stage == 'P':
            stage = 'P01'
        else:
            raise ValueError("Invalid stage.")
        return ''.join([race_abbr, date[0:4], stage])


# %%
class DataExtracter(object):
    """用于从原始数据提取出特定的变量，集中到统一的文件中用于聚类."""

    def __init__(self, root=None):
        self.root = ROOT if not root else root
        self.source_dir = os.path.join(self.root, r"Converted_Tidied")
        self.extract_dir = os.path.join(self.root, r"Converted_Extracted")
        if not os.path.exists(self.extract_dir):
            os.makedirs(self.extract_dir)
        return

    def extract_all(self, races='Grand Tour', seasons='all', result_types=('SC', 'SGC', 'GC')):
        """The adapter method for batch extracting information from data files.

        By default, only the Grand Tours and Stage Classification, Stage General Classification
        and General Classification will be extracted.

        :param races: Can be 'Grand Tour' (default), 'all', 'multi', 'single', the full name of a single race,
            or a list of full names of races.
        :param seasons: Can be 'all' (default, from 2009 to 2019), a single season of int or str type,
            or a list of seasons each of int or str type.
        :param result_types: By default only Stage Classification, Stage General Classification
            and General Classification results will be extracted.
        """
        path_tidy_log = os.path.join(self.root, r"Converted_Raw\tidy_log.txt")
        tidy_log = log.auto_read_log(path_tidy_log)
        path_extract_log = os.path.join(self.source_dir, r"extract_log.txt")
        extract_log = log.auto_read_log(path_extract_log)

        if type(races) == str:
            if races == 'Grand Tour':
                races = ['Tour de France', "Giro d'Italia", 'Vuelta a España']
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

        if type(seasons) == str:
            if seasons == 'all':
                seasons = global_vars.get_value('SEASONS')
            else:
                seasons = [seasons]
        elif type(seasons) == int:
            seasons = [str(seasons)]
        else:
            seasons = [str(season) for season in seasons]

        try:
            for race in races:
                for season in seasons:
                    extract_log = self.extract(self.source_dir, race, season, result_types, tidy_log, extract_log)
                    log.auto_write_log(extract_log, path_extract_log)
        finally:
            log.auto_write_log(extract_log, path_extract_log)
        return

    def extract(self, source_dir, race, season, result_types, tidy_log, extract_log):
        """Extract information for a single race and year.
        
        return: Extract log.
        """
        save_dir = os.path.join(self.extract_dir, race)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file_name = '_'.join([race, season, 'extracts.csv'])

        if save_file_name not in extract_log.keys() or \
                extract_log[save_file_name] == 'N':
            extract_df, file_path_list = self.create_start_list(source_dir, race, season)
            start_list_dict = {}
            for row in extract_df.iterrows():  # Hash the start list. Dict structure: {Cyclist ID: row_index}
                start_list_dict.update({row[1]['Cyclist ID']: row[0]})
            for file_path in file_path_list:
                extract_df = self.add_extract_info(file_path, start_list_dict, extract_df, result_types, tidy_log)
            basics.write_csv_bom(extract_df, os.path.join(save_dir, save_file_name))
            extract_log[save_file_name] = 'Y'

        return extract_log

    @staticmethod
    def create_start_list(source_dir, race, season,
                          fields=('Full Name', 'Country', 'Cyclist ID', 'Team', 'Gender', 'Age')):
        """Create start list and extract the cyclists' demographic information, from the FC_GC file.

        Including: Full name, nationality, cyclist ID, team, gender, and age.

        :return: The start list for specified race and season, and the list of all file paths in this directory.
        """
        print("Creating start list for {} {}".format(race, season))

        cur_dir = os.path.join(source_dir, race, season)
        file_path_list = basics.get_file_list(cur_dir, extension='.csv')
        for file in file_path_list:
            if 'FC_GC' in file:
                with open(file, 'r', encoding=ENCODING) as fr:
                    source_data = pd.read_csv(fr)
                    fr.close()
                break
        start_list = pd.DataFrame(source_data[[field for field in fields]])

        return start_list, file_path_list

    @staticmethod
    def add_extract_info(source_file_path, start_list_dict, extract_df, result_types, tidy_log,
                         extract_fields=('Rank', 'Rank_Norm', 'Time Lag_Norm')):
        """Add information to the extract data file.

        :return: The updated dataframe storing extracted information.
        """
        file_name = os.path.split(source_file_path)[1]
        result_type, stage_type = os.path.splitext(file_name)[0].split('_')[3:]

        if result_type in result_types and tidy_log[file_name] == 'Y':  # Only extract from tidied files; else pass
            with open(source_file_path, 'r', encoding=ENCODING) as fr:
                source_data = pd.read_csv(fr)
                fr.close()
            print("    Extracting information from {}".format(file_name))

            new_fields = {}
            for field in extract_fields:  # Header format: Race ID_ResultType_StageType_Variable
                new_fields[field] = '_'.join([source_data['Race ID'][0], result_type, stage_type, field])
            for row in source_data.iterrows():
                index = start_list_dict.get(row[1]['Cyclist ID'])
                if index is not None:
                    for field in extract_fields:
                        extract_df.loc.__setitem__((index, new_fields[field]), row[1][field])
                else:  # If no cyclist matches (but this is not supposed to happen)
                    print("    {} (ID: {}) not found in the start list"
                          .format(row[1]['Full Name'], row[1]['Cyclist ID']))

        return extract_df


# %%
class VarGenerator(object):
    """从原始变量数据计算衍生变量，直接用于聚类模型."""

    def __init__(self, root=None):
        self.root = ROOT if not root else root
        self.cluster_root = os.path.join(root, 'For_Clustering')
        return

    def gen_vars_all(self, race_range='Grand Tour', year_range='all', var_list=None):
        """ To calculate variables used directly for clustering and write them into data files """
        var_list = self._gen_var_list(var_list)

        if race_range == 'Grand Tour':
            race_range = ['Tour de France', "Giro d'Italia", 'Vuelta a España']
        elif type(race_range) == str:
            race_range = [race_range]

        for race in race_range:
            file_dir = os.path.join(self.cluster_root, race)
            file_list = basics.get_file_list(file_dir, extension='.csv')
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
        basics.write_csv_bom(gen_data, source_path)
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
                    if basics.is_number(row[1][stage]):
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
                        if basics.is_number(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'IRR' in var:
                    for stage in stage_list:
                        if 'TT' not in stage and basics.is_number(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'TT' in var:
                    for stage in stage_list:
                        if 'TT' in stage and basics.is_number(row[1][stage]):
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
                    if basics.is_number(row[1]['stage_max_SGC']):
                        source_data.loc.__setitem__((row[0], var), row[1]['FC_GC_IRR_Rank'] - row[1]['stage_max_SGC'])
            else:
                if not stage_list:
                    for col in cols:
                        if 'SGC' in col and 'Rank' in col and 'Norm' not in col:
                            stage_list.append(col)
                for row in source_data.iterrows():
                    max_list = [999, 0]  # 前面的表示最高SGC，后面的表示对应的赛段；注意高排名对应低数值
                    for stage in stage_list:
                        if basics.is_number(row[1][stage]) and row[1][stage] < max_list[0]:
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
                        if basics.is_number(row[1][stage]):
                            temp_list.append(row[1][stage])
                elif 'IRR' in var:
                    for stage in stage_list:
                        if 'TT' not in stage and basics.is_number(row[1][stage]):
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
