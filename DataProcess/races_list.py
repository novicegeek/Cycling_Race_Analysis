# -*- coding: utf-8 -*-
"""
Create list and meta-information of cycling races. Data source: La FlammeRouge.
Information (fields) included:
-ID (E.g., TDF2012S01, using the NOMINAL stage number)
-Nominal Stage Number (The prologue will remain as it was)
-Actual Stage Number (The stage will be numbered according to its ACTUAL order of taking place.
  I.e., a prologue will be treated equally as other stage and will thus be stage 1 instead.)
-Race (E.g., Tour de France)
-Is Multi-Day
-Has Prologue (Whether this edition had a prologue)
-Is Overall Race (Whether this is a single stage within a multi-day tour, or the overall tour as a whole)
-Date (8-digits)
-Depart
-Arrive
-Length
-Type (ITT, TTT, IRR)
-Profile (Medium Mountain, High Mountain, etc.)  # Question: The profile for Time Trials?
-TBC...
"""


import json
import os
import numpy as np
import pandas as pd
import global_vars
import basics


ENCODING = global_vars.get_value('ENCODING')
HALF_RECORD = global_vars.get_value('HALF-RECORD')
MULTI_STAGES = global_vars.get_value('MULTI-STAGES')
NO_RECORD = global_vars.get_value('NO-RECORD')
ROOT = global_vars.get_value('ROOT')
with open(os.path.join(ROOT, r"Codes\DataAcquire\competition_codes.json"), 'r', encoding='utf-8') as fr:
    RACE_CODES = json.load(fr)
    fr.close()
TOLERANCE = 1e-8


class RacesList(object):
    """Create races list and other information."""

    def __init__(self):
        self.source_dir = os.path.join(ROOT, r"MetaData\races_meta_data")
        self.races_list_path = os.path.join(ROOT, r"MetaData\races_list.csv")

    def create_list(self,
                    races='all',
                    seasons='all',
                    overwrite=False):
        """Create races list.

        :param races: What races to take into account. By default only Grand Tours.
        :param seasons: What seasons to take into account. By default 'all', including all seasons in the meta files.
        :param overwrite: Boolean. Whether to overwrite the race if it already exists in the list.
        """
        try:
            with open(self.races_list_path, 'r', encoding=ENCODING) as fr:
                cur_list = pd.read_csv(self.races_list_path)
                fr.close()
            # Hash existing ID list to accelerate matching
            cur_list_ids_dict = dict([item[-1::-1] for item in cur_list['ID'].items()])
        except FileNotFoundError:
            cur_list = pd.DataFrame()
            cur_list_ids_dict = {}

        races = basics.get_races_list(races)
        seasons = basics.get_seasons_list(seasons)

        for race in races:
            workbook = pd.read_excel(os.path.join(self.source_dir, race + '.xlsx'),  # Gets a dict
                                     sheet_name=None, encoding=ENCODING)
            is_multi_stage = 1 if race in MULTI_STAGES else 0
            race_abbr = RACE_CODES[race]
            race_meta_df = pd.DataFrame()
            for year, cur_sheet in workbook.items():  # year is the sheet name; cur_sheet is a dataframe
                if year not in seasons:
                    continue
                print("---------- Examining {} {} ----------".format(race, year))
                actual_stage_count = 0
                last_stage = np.nan
                has_prologue = 1 if cur_sheet['NUM'][0] == 'P' else 0
                total_length = 0
                for cur_row in cur_sheet.iterrows():
                    if not pd.isna(cur_row[1]['NUM']):  # This is stage information
                        stage_num = cur_row[1]['NUM']
                        print("    ------ Examining stage {} ------".format(stage_num))
                        stage_meta_df = pd.DataFrame({
                            'ID': basics.create_race_id(race_abbr, year, is_multi_stage,
                                                        from_race_meta=True, stage=cur_row[1]['NUM']),
                            'Nominal Stage Number': int(float(stage_num)) if self._is_int(stage_num) else stage_num,
                            'Actual Stage Number': self._get_actual_stage_number(has_prologue, cur_row[1]),
                            'Last Stage': last_stage,
                            'Race': race,
                            'Year': year,
                            'Is Multi-Stage': is_multi_stage,
                            'Has Prologue': has_prologue,
                            'Is A Stage': 1 if is_multi_stage else np.nan,
                            'Date': self._get_date(cur_row[1], source='La FlammeRouge'),
                            'Depart': cur_row[1]['DEPART AND ARRIVE'].split('>')[0].strip(),
                            'Arrive': cur_row[1]['DEPART AND ARRIVE'].split('>')[1].strip(),
                            'Length': cur_row[1]['LENGTH'],
                            'Type': self._get_stage_type(cur_row[1]),
                            'Profile': cur_row[1]['TYPE']  # For now, the profile of a time trial is not clear.
                        }, index=[0])
                        last_stage = stage_meta_df['ID'][0]
                        total_length += cur_row[1]['LENGTH']
                        if cur_list_ids_dict.get(stage_meta_df['ID'][0]) is None:
                            cur_list = pd.concat([cur_list, stage_meta_df], ignore_index=True, sort=False)
                            cur_list_ids_dict.update([(stage_meta_df['ID'][0], len(cur_list_ids_dict))])
                            print("        -- Stage {} of {} {} newly appended --"
                                  .format(stage_num, race, year))
                        elif overwrite:
                            stage_row_index = cur_list_ids_dict[stage_meta_df['ID'][0]]
                            for col in stage_meta_df.columns:
                                cur_list.loc.__setitem__((stage_row_index, col), stage_meta_df[col][0])
                            cur_list.loc.__setitem__((stage_row_index, 'Winner Avg Speed'), np.nan)
                            cur_list.loc.__setitem__((stage_row_index, 'Median Avg Speed'), np.nan)
                            print("        -- Stage {} of {} {} overwritten --"
                                  .format(stage_num, race, year))
                        else:
                            print("        -- Stage {} of {} {} already exists --"
                                  .format(stage_num, race, year))
                        actual_stage_count += 1
                    elif not pd.isna(cur_row[1]['TYPE']):  # This is race information
                        key = cur_row[1]['TYPE']  # Now the titles are indices (like a transposition)
                        value = cur_row[1]['LENGTH']
                        if key == 'Total distance':
                            if abs(value - total_length) > TOLERANCE:
                                print("        -- Total length differs from the sum of individual lengths --")
                            race_meta_df.loc.__setitem__((0, key), value)
                            race_meta_df.loc.__setitem__((0, 'Total stages'), actual_stage_count)
                            race_meta_df.loc.__setitem__((0, 'Average distance'), value / actual_stage_count)
                        else:
                            if self._is_int(value):
                                value = int(value)
                            race_meta_df.loc.__setitem__((0, key), value)
                    else:
                        pass
                if is_multi_stage:
                    race_meta_df = pd.DataFrame(dict(dict(race_meta_df), **{
                        'ID': basics.create_race_id(race_abbr, year, is_multi_stage,
                                                    from_race_meta=True, stage=np.nan),
                        'Last Stage': last_stage,
                        'Race': race,
                        'Year': year,
                        'Is Multi-Stage': is_multi_stage,
                        'Has Prologue': has_prologue,
                        'Is A Stage': 0,
                        'Length': race_meta_df.loc.__getitem__((0, 'Total distance')),
                        'Type': 'OVR'
                    }))
                    if cur_list_ids_dict.get(race_meta_df['ID'][0]) is None:
                        cur_list = pd.concat([cur_list, race_meta_df], ignore_index=True, sort=False)
                        cur_list_ids_dict.update([(race_meta_df['ID'][0], len(cur_list_ids_dict))])
                        print("    ------ {} {} newly appended ------".format(race, year))
                    elif overwrite:
                        race_row_index = cur_list_ids_dict[race_meta_df['ID'][0]]
                        for col in race_meta_df.columns:
                            cur_list.loc.__setitem__((race_row_index, col), race_meta_df[col][0])
                        cur_list.loc.__setitem__((race_row_index, 'Winner Avg Speed'), np.nan)
                        cur_list.loc.__setitem__((race_row_index, 'Median Avg Speed'), np.nan)
                        print("        -- {} {} overwritten --".format(race, year))
                    else:
                        print("    ------ {} {} already exists ------".format(race, year))
                basics.write_csv_bom(cur_list, self.races_list_path)

        for row in cur_list.iterrows():
            if row[1]['ID'] not in HALF_RECORD + NO_RECORD:
                has_records = 1
            elif row[1]['ID'] in NO_RECORD:
                has_records = 0
            else:
                has_records = 0.5
            cur_list.loc.__setitem__((row[0], 'Has Records'), has_records)
        basics.write_csv_bom(cur_list, self.races_list_path)
        return

    @staticmethod
    def _get_actual_stage_number(has_prologue, row_data):
        """Get the actual stage number from the nominal data.

        :param has_prologue: Boolean. Whether this race had a prologue.
        :row_data: The row of data being examined.
        :return: Int.
        """
        if not has_prologue:
            actual_stage_number = int(row_data['NUM'])
        else:
            if row_data['NUM'] == 'P':
                actual_stage_number = 1
            else:
                actual_stage_number = int(row_data['NUM']) + 1
        return actual_stage_number

    @staticmethod
    def _get_date(row_data, source='La FlammeRouge'):
        """Get the 8-character date code from the original format."""
        months_dict = {'January': '01', 'February': '02', 'March': '03',
                       'April': '04', 'May': '05', 'June': '06',
                       'July': '07', 'August': '08', 'September': '09',
                       'October': '10', 'November': '11', 'December': '12'}
        if source == 'La FlammeRouge':  # The format is like 'Saturday 3 July 2010'.
            day_of_the_week, day, month, year = row_data['DATE'].split(' ')
            day = '0' * (2 - len(day)) + day
            return year + months_dict[month] + day
        else:
            return

    @staticmethod
    def _get_stage_type(row_data):
        """Get the ABBREVIATION of the stage type."""
        stage_type = row_data['TYPE']
        if 'Time Trial' in stage_type:
            return ''.join([part[0].upper() for part in stage_type.split(' ')])
        else:
            return 'IRR'

    @staticmethod
    def _is_int(num):
        """Determine if the input is an integer or not."""
        try:
            return abs(float(num) - int(float(num))) < TOLERANCE
        except ValueError or TypeError:
            return False
