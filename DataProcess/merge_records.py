# -*- coding: utf-8 -*-
"""Merge record files into summarization for further processing."""


import os
import time
import pandas as pd
import basics
import global_vars


ENCODING = global_vars.get_value('ENCODING')
NULL_HEADERS = ('Full Name', 'Country', 'Cyclist ID', 'Team', 'Gender', 'Age')
ROOT = global_vars.get_value('ROOT')


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
