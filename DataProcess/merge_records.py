# -*- coding: utf-8 -*-
"""Merge record files into summarization for further processing."""


import copy
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

        NOTE: This method always write a new file, instead of appending records to an existing file.

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
