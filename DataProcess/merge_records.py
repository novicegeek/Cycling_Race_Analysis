# -*- coding: utf-8 -*-
"""Merge record files into summarization for further processing."""


import copy
import json
import os
import time
import numpy as np
import pandas as pd
import basics
import global_vars


ENCODING = global_vars.get_value('ENCODING')
NULL_HEADERS = ('Full Name', 'Country', 'Cyclist ID', 'Team', 'Gender', 'Age')
ROOT = global_vars.get_value('ROOT')
TOLERANCE = 1e-8


class MergeRecords(object):

    def __init__(self):
        self.merge_dir = os.path.join(ROOT, r"Merged")
        self.source_dir = os.path.join(ROOT, r"Converted_Extracted")
        if not os.path.exists(self.merge_dir):
            os.makedirs(self.merge_dir)
        return


class MergeByCyclistSplitBySeason(MergeRecords):
    """Merge records for every individual cyclist, forming season-wise files."""

    def __init__(self):
        super().__init__()
        return

    def create(self, races='Grand Tour', seasons='all', result_types=('SC', 'GC'), include_ttt=False):
        """
        NOTE: This method always write a new file, instead of appending records to an existing file. For updating,
        use the MergeByCyclistSplitBySeason.update() method.

        :param races: Can be 'Grand Tour' (default), 'all', 'multi', 'single', the full name of a single race,
            or a list of full names of races.
        :param seasons: Can be 'all' (default, from 2009 to 2019), a single season of int or str type,
            or a list of seasons each of int or str type.
        :param result_types: By default 'SC'. Notice that this parameter should be consistent with the setting of races.
        :param include_ttt: Boolean. Whether to include TTT stages. By default False.
        """
        seasons = basics.get_seasons_list(seasons)

        for season in seasons:
            self._merge_by_cyclist_split_by_season(season, races, result_types, include_ttt, option='create')
        return

    def update(self, races='Grand Tour', seasons='all', result_types=('SC', 'GC'), include_ttt=False):
        """Adding new records to an existing file. Similar protocol to MergeByCyclistSplitBySeason.create() method."""
        seasons = basics.get_seasons_list(seasons)

        for season in seasons:
            self._merge_by_cyclist_split_by_season(season, races, result_types, include_ttt, option='update')
        return

    def _merge_by_cyclist_split_by_season(self, season, races, result_types, include_ttt=False, option='create'):
        """Merge records for every individual cyclist, forming season-wise files.

        By default, this method write a new file, instead of appending records to an existing file.

        :param season: A single year of str type.
        """
        start = time.clock()
        races_param = races
        print("---------- Start merging {} race(s) in {} ----------".format(races_param, season))
        races = basics.get_races_list(races)
        result_types = basics.get_result_types_list(result_types)

        merge_file_name = '_'.join(
            ['merge_by_cyclist', season, '&'.join([result_type for result_type in result_types])]
        ) + '.csv'
        merge_file_path = os.path.join(self.merge_dir, merge_file_name)
        if option == 'create':
            merged_df = pd.DataFrame()
        elif option == 'update':
            try:
                with open(merge_file_path, 'r', encoding=ENCODING) as fr:
                    merged_df = pd.read_csv(fr)
                    fr.close()
            except FileNotFoundError:
                print("Merged {} records for {} races in {} doesn't exist. Will create a new file now."
                      .format(result_types, races, season))
                return self._merge_by_cyclist_split_by_season(season, races, result_types, include_ttt, option='create')
        else:
            print("Operation unsupported.")
            return
        merged_dict = {}
        for row in merged_df.iterrows():
            merged_dict.update({row[1]['Cyclist ID']: row[0]})

        for race in races:
            source_file_name = '_'.join([race, season, 'extracts']) + '.csv'
            source_file_path = os.path.join(self.source_dir, race, source_file_name)
            with open(source_file_path, 'r', encoding=ENCODING) as fr:
                source_data = pd.read_csv(fr)
                fr.close()

            valid_fields = list(source_data.columns)
            for header in NULL_HEADERS:
                valid_fields.remove(header)
            location = 0
            while location < len(valid_fields):  # 不能用for循环，因为valid_fields发生改变之后指针还是按原来一样向前走，不会回退
                result_type, stage_type = valid_fields[location].split('_')[1:3]
                if (stage_type == 'TTT' and not include_ttt) or (result_type not in result_types):
                    valid_fields.remove(valid_fields[location])
                else:
                    location += 1

            for row in source_data.iterrows():
                index = merged_dict.get(row[1]['Cyclist ID'])
                if index is None:
                    index = len(merged_df)
                    for header in NULL_HEADERS:
                        merged_df.loc.__setitem__((index, header), row[1][header])
                    merged_dict.update({row[1]['Cyclist ID']: index})
                for field in valid_fields:
                    merged_df.loc.__setitem__((index, field), row[1][field])

            basics.write_csv_bom(merged_df, merge_file_path)
            print("    Records for {} {} merged to {} successfully".format(race, season, merge_file_name))
        print("---------- Records for {} race(s) in {} merged successfully. Path: {} ----------"
              .format(races_param, season, merge_file_path))
        print("    ------ Time cost: {} ------".format(time.clock() - start))
        return


class GenerateMetaByCyclistSplitBySeason(MergeByCyclistSplitBySeason):
    """Generate meta-data in files generated by class MergeByCyclistSplitBySeason."""

    def __init__(self):
        super().__init__()
        self.races_info_file_path = os.path.join(ROOT, r"MetaData\races_list.csv")
        return

    def gen_meta(self,
                 seasons='all',
                 profiles=('Plain', 'Medium', 'High', 'Individual'),
                 stats=('Rank', 'Rank_Norm', 'Time Lag_Norm'),
                 in_place=True):
        """Generate meta-data based on extracted information.

        Fields include:
        1. Number of races (one stage within a multi-stage race counts as one race hereby) finished normally,
            counting profile-wise and difficulty-wise.
            I.e., only include those with a valid ranking and exclude DNF/DNS/DSQ/OTL cyclists.
        2. Average performance statistics: Average rank/rank_norm/time_lag_norm.
        3. Average profile-specific performance statistics: Similar to the above.
        4. Average difficulty-specific performance statistics: Needs classification of race stages,
            generated by other class (maybe classified by the percentage of starters of this stage).
        5. Self-normalized profile-specific performance: Set the average performance of a cyclist in plain stages as 1,
            then normalized his average performance in other profiles by division.
        6. Self-normalized difficulty specific performance: Similar to 5.
        """
        with open(self.races_info_file_path, 'r', encoding=ENCODING) as fr:
            races_info = pd.read_csv(fr)
            fr.close()
        races_info_dict = dict([(row[1]['ID'], row[0]) for row in races_info.iterrows()])

        seasons = basics.get_seasons_list(seasons)
        for item in os.listdir(self.merge_dir):
            if os.path.splitext(item)[1] == '.csv' and item.split('_')[3] in seasons:
                print("---------- Generate meta-data for {} ----------".format(item))
                source_path = os.path.join(self.merge_dir, item)
                if in_place:
                    with open(source_path, 'r', encoding=ENCODING) as fr:
                        write_data = pd.read_csv(fr)
                        fr.close()
                    write_path = source_path
                else:
                    with open(source_path, 'r', encoding=ENCODING) as fr:
                        source_data = pd.read_csv(fr)
                        fr.close()
                    write_data = copy.deepcopy(source_data[list(NULL_HEADERS)])
                    write_name = 'meta_' + item
                    write_path = os.path.join(self.merge_dir, write_name)

                start = time.clock()
                cycle_start = time.clock()
                # Generate empty dictionary. Structure: {profile_1: {race_1_id: race_1_prefix, ...}, ...}
                # Race prefix is the first 3 parts of the field name, like GDI2011S15_SC_IRR
                races_dict_by_profile = dict([(profile, {}) for profile in profiles])
                # Add columns to corresponding list of fields, so that during the matching of generating meta-data
                # variables, no need to extract race information for every cyclist, every column (m * n complexity)
                for col in source_data.columns:  # Generate dictionaries storing different batches of fields
                    if col in NULL_HEADERS:
                        continue
                    race_id = col.split('_')[0]
                    try:
                        profile = races_info['Profile'][races_info_dict[race_id]]
                    except KeyError:
                        print("  Race {} not in the races list".format(race_id))
                        continue
                    if pd.isna(profile):  # This is a row for overall race
                        continue
                    else:
                        profile = profile.split(' ')[0]
                        if races_dict_by_profile[profile].get(race_id) is None:
                            races_dict_by_profile[profile][race_id] = '_'.join(col.split('_')[0:3])
                # Generate meta-data for every cyclist
                last_write = 0
                for row in source_data.iterrows():
                    index = row[0]
                    # Create empty dictionary to store performance stats for the current cyclist
                    stats_dict = dict([(profile, {}) for profile in profiles])
                    stats_dict['Total'] = {}
                    for profile, sub_dict in stats_dict.items():
                        if profile != 'Total':  # Store the list of all relevant numbers
                            sub_dict.update([(stat, []) for stat in stats])
                        else:  # For total statistics, the sub-dictionary stores the sum instead of the whole list
                            sub_dict.update([(stat, 0) for stat in stats])
                    # Scan and add the stats to the dictionary profile by profile, and stats by stats
                    for profile, races_dict in races_dict_by_profile.items():
                        for race_id, race_prefix in races_dict.items():
                            if not pd.isna(source_data[race_prefix + '_Rank'][index]):  # Finished with a valid ranking
                                for stat in stats:
                                    cur_stat = row[1]['_'.join([race_prefix, stat])]
                                    stats_dict[profile][stat].append(cur_stat)
                    # Add profile meta-data to the current dataframe
                    total_count = 0
                    for profile in profiles:
                        profile_count = len(stats_dict[profile]['Rank'])
                        total_count += profile_count
                        write_data.loc.__setitem__((index, ' '.join(['Total', profile, 'Races'])), profile_count)
                        for stat in stats:
                            stat_sum = sum(stats_dict[profile][stat])
                            if profile_count != 0:  # Check before every division
                                stat_average = stat_sum / profile_count
                            else:
                                stat_average = np.nan
                            write_data.loc.__setitem__(
                                (index, ' '.join(['Average', profile, stat])), stat_average
                            )
                            if write_data[' '.join(['Average Plain', stat])][index] > TOLERANCE:
                                norm_stat_average = stat_average / write_data[' '.join(['Average Plain', stat])][index]
                            else:
                                norm_stat_average = np.nan
                            write_data.loc.__setitem__(
                                (index, ' '.join(['Average', profile, stat, 'Normalized to Plain'])),
                                norm_stat_average
                            )
                            stats_dict['Total'][stat] += stat_sum
                    # Add total meta-data
                    write_data.loc.__setitem__((index, 'Total Races'), total_count)
                    for stat in stats:
                        if total_count != 0:
                            stat_average = stats_dict['Total'][stat] / total_count
                        else:
                            stat_average = np.nan
                        write_data.loc.__setitem__((index, ' '.join(['Total Average', stat])), stat_average)
                        if write_data[' '.join(['Average Plain', stat])][index] > TOLERANCE:
                            norm_stat_average = stat_average / write_data[' '.join(['Average Plain', stat])][index]
                        else:
                            norm_stat_average = np.nan
                        write_data.loc.__setitem__(
                            (index, ' '.join(['Total Average', stat, 'Normalized to Plain'])),
                            norm_stat_average
                        )
                    last_write += 1
                    if not last_write % 50:
                        basics.write_csv_bom(write_data, write_path)
                        print("--- Rewrite merged file. ---\n"
                              "        Cyclists scanned: {}\n"
                              "        The last one: {}".format(last_write, row[1]['Full Name']))
                        print("        Time cost of last write cycle: {}s".format(time.clock() - cycle_start))
                        cycle_start = time.clock()
                basics.write_csv_bom(write_data, write_path)
                print("---------- Meta-data generated for {}. Time cost: {} ----------\n"
                      .format(item, time.clock() - start))
        return


class MergeByCyclistPoolSeason(MergeRecords):
    """Merge records for every individual cyclist, pooling the records from multiple seasons."""

    def __init__(self):
        super().__init__()
        return

    def create(self, races='all', seasons='all', result_types=('SC', 'GC'), include_ttt=False, meta_only=True):
        """
        NOTE: This method always write a new file, instead of appending records to an existing file. For updating,
        use the MergeByCyclistPoolSeason.update() method.

        :param races: Can be 'all' (default), 'Grand Tour', 'multi', 'single', the full name of a single race,
            or a list of full names of races.
        :param seasons: Can be 'all' (default, from 2009 to 2019), a single season of int or str type,
            or a list of seasons each of int or str type.
        :param result_types: By default 'SC'. Notice that this parameter should be consistent with the setting of races.
        :param include_ttt: Boolean. Whether to include TTT stages. By default False.
        :param meta_only: Boolean. If true (default), only meta-data of the cyclists results from different perspectives
            will be remained (e.g., total plain races, average plain rank, etc.), not individual records of races.
        """
        return self._merge_by_cyclist_pool_season(seasons, races, result_types, include_ttt, meta_only, option='create')

    def update(self, races='all', seasons='all', result_types=('SC', 'GC'), include_ttt=False, meta_only=True):
        """Adding new records to an existing file. Similar protocol to MergeByCyclistSplitBySeason.create() method."""
        return self._merge_by_cyclist_pool_season(seasons, races, result_types, include_ttt, meta_only, option='update')

    def _merge_by_cyclist_pool_season(self, seasons, races, result_types, include_ttt, meta_only=True, option='create'):
        """Merge records for every individual cyclist from multiple seasons, forming a single file.

        By default, this method write a new file, instead of appending records to an existing file.
        """
        start = time.clock()

        seasons = basics.get_seasons_list(seasons)
        races = basics.get_races_list(races)
        result_types = basics.get_result_types_list(result_types)
        self.merge_dir
        pass


class GenerateCyclistMeta(object):
    """Generate documents storing the meta records of individual cyclists."""

    def __init__(self):
        self.merge_dir = os.path.join(ROOT, r"Cyclist_Meta")
        self.races_list_path = os.path.join(ROOT, r"MetaData\races_list.csv")
        self.source_dir = os.path.join(ROOT, r"Cyclist_Records")
        return

    def gen_meta(self):
        """
        Generate meta-data on:
        1. Total all/all irr/plain/medium/high/itt races (with a valid ranking)
        2. Average rank/rank_norm/time lag_norm/speed rel to winner/speed rel to median for
            all/all irr/plain/medium/high/itt races
        """
        start = time.clock()
        with open('competition_codes_rev.json', 'r', encoding=ENCODING) as fr:
            competition_codes_rev = json.load(fr)
            fr.close()
        with open(self.races_list_path, 'r', encoding=ENCODING) as fr:
            races_list = pd.read_csv(fr)
            fr.close()
        races_list_dict = {}
        races_list_dict.update([(row[1]['ID'], row[0]) for row in races_list.iterrows()])
        attrs = ['Num', 'Avg Rank', 'Avg Rank_Norm', 'Avg Time Lag_Norm',
                 'Avg Speed Rel to Winner', 'Avg Speed Rel to Median']

        count = 0
        for source_file in os.listdir(self.source_dir):
            source_path = os.path.join(self.source_dir, source_file)
            with open(source_path, 'r', encoding=ENCODING) as fr:
                source_records = json.load(fr)
                fr.close()

            cyclist_meta_dict_sc = dict([
                (profile, {}) for profile in ['Total', 'IRR', 'Plain', 'Medium', 'High', 'ITT']
            ])
            cyclist_meta_dict_gc = dict([
                (race_cat, {}) for race_cat in ['Total', 'Grand Tour', 'Other Multi', 'Single']
            ])
            for profile_dict in cyclist_meta_dict_sc.values():
                profile_dict.update([(attr, []) for attr in attrs])
            for cat_dict in cyclist_meta_dict_gc.values():
                cat_dict.update([(attr, []) for attr in attrs])

            for race_id, race_record in source_records.items():
                for result_type, type_record in race_record.items():
                    if pd.isna(type_record['Rank']):
                        continue
                    else:
                        race_index = races_list_dict[race_id]
                        race_type = races_list['Type'][race_index]
                    if result_type == 'GC':
                        race_name = competition_codes_rev[race_id[:3]]
                        if race_name in global_vars.get_value('GRAND TOUR'):
                            race_cat = 'Grand Tour'
                        elif race_name in global_vars.get_value('MULTI-STAGES'):
                            race_cat = 'Other Multi'
                        else:
                            race_cat = 'Single'
                        for attr in attrs:
                            if attr == 'Num':
                                new_append = 1 if pd.notna(type_record['Rank']) else 0
                            elif 'Speed' in attr:
                                new_append = type_record[attr]
                            else:
                                new_append = type_record[attr.split('Avg ')[1]]
                            cyclist_meta_dict_gc['Total'][attr].append(new_append)
                            cyclist_meta_dict_gc[race_cat][attr].append(new_append)
                    if race_type in ['IRR', 'ITT'] and result_type in ['SC', 'GC']:  # 注意：单日赛会同时被添加到gc和sc两个文件里
                        profile = race_type if race_type == 'ITT' else races_list['Profile'][race_index].split(' ')[0]
                        for attr in attrs:
                            if attr == 'Num':
                                new_append = 1 if pd.notna(type_record['Rank']) else 0
                            elif 'Speed' in attr:
                                new_append = type_record[attr]
                            else:
                                new_append = type_record[attr.split('Avg ')[1]]
                            cyclist_meta_dict_sc['Total'][attr].append(new_append)
                            cyclist_meta_dict_sc[profile][attr].append(new_append)
                            if profile != 'ITT':
                                cyclist_meta_dict_sc['IRR'][attr].append(new_append)
            cyclist_id = os.path.splitext(source_file)[0]
            gc_dir = os.path.join(self.merge_dir, 'GC')
            sc_dir = os.path.join(self.merge_dir, 'SC')
            if not os.path.exists(gc_dir):
                os.makedirs(gc_dir)
            if not os.path.exists(sc_dir):
                os.makedirs(sc_dir)
            with open(os.path.join(gc_dir, '_'.join([cyclist_id, 'full']) + '.json'), 'w', encoding=ENCODING) as fw:
                json.dump(cyclist_meta_dict_gc, fw)
                fw.close()
            with open(os.path.join(sc_dir, '_'.join([cyclist_id, 'full']) + '.json'), 'w', encoding=ENCODING) as fw:
                json.dump(cyclist_meta_dict_sc, fw)
                fw.close()
            for cat_dict in cyclist_meta_dict_gc.values():
                num = sum(cat_dict['Num'])
                for attr in cat_dict.keys():
                    if attr == 'Num':
                        cat_dict[attr] = num
                    else:
                        cat_dict[attr] = np.nan if num == 0 else np.nansum(cat_dict[attr]) / num
            for profile_dict in cyclist_meta_dict_sc.values():
                num = sum(profile_dict['Num'])
                for attr in profile_dict.keys():
                    if attr == 'Num':
                        profile_dict[attr] = num
                    else:
                        profile_dict[attr] = np.nan if num == 0 else np.nansum(profile_dict[attr]) / num
            with open(os.path.join(gc_dir, '_'.join([cyclist_id, 'avg']) + '.json'), 'w', encoding=ENCODING) as fw:
                json.dump(cyclist_meta_dict_gc, fw)
                fw.close()
            with open(os.path.join(sc_dir, '_'.join([cyclist_id, 'avg']) + '.json'), 'w', encoding=ENCODING) as fw:
                json.dump(cyclist_meta_dict_sc, fw)
                fw.close()
            count += 1
            if not count % 100:
                print("{} cyclists merged. Total time: {}".format(count, time.clock() - start))

        return

    def merge_meta(self):
        cyclists_list_path = os.path.join(ROOT, r"MetaData\cyclists_list.csv")
        with open(cyclists_list_path, 'r', encoding=ENCODING) as fr:
            cyclists_list = pd.read_csv(fr)
            fr.close()
        cyclists_dict = dict([
            (row[1]['ID'], row[1]['Full Name']) for row in cyclists_list.iterrows()
        ])
        self._merge_meta_by_type('GC', self.merge_dir, cyclists_dict)
        self._merge_meta_by_type('SC', self.merge_dir, cyclists_dict)
        return

    def _merge_meta_by_type(self, result_type, to_dir, cyclists_dict):
        if os.path.isdir(to_dir):
            source_dir = os.path.join(self.merge_dir, result_type)
            merged_df = pd.DataFrame()
            count = 0
            for source_name in os.listdir(source_dir):
                if 'avg' in source_name:
                    cyclist_id = source_name.split('_')[0]
                    to_merge_dict = {
                        'ID': cyclist_id,
                        'Full Name': cyclists_dict[cyclist_id],
                        'Country': cyclist_id[:3]
                    }
                    source_path = os.path.join(source_dir, source_name)
                    with open(source_path, 'r', encoding=ENCODING) as fr:
                        source_data = json.load(fr)
                        fr.close()
                    for cat, cat_dict in source_data.items():
                        for attr, value in cat_dict.items():
                            to_merge_dict[': '.join([cat, attr])] = value
                    merged_df = pd.concat([merged_df, pd.DataFrame(to_merge_dict, index=[0])],
                                          ignore_index=True, sort=False)
                    count += 1
                    if not count % 200:
                        print("{} cyclists merged for {} results".format(count, result_type))
            basics.write_csv_bom(merged_df, os.path.join(to_dir, 'cyclist_meta_merged_' + result_type + '.csv'))
            return 1
        else:
            print("Invalid directory to export the merged file.")
            return 0
