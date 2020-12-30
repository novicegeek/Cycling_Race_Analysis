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


import os
import json
import pandas as pd
import pandas.core.series
import numpy as np
import global_vars
ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')
with open(os.path.join(ROOT, r"Codes\DataAquire\competition_codes.json"), 'r', encoding='utf-8') as fr:
    RACE_CODES = json.load(fr)
    fr.close()
MULTI_STAGES = ['Tour de France', "Giro d'Italia", 'Vuelta a España']
TOLERANCE = 1e-8


class RacesList(object):
    """Create races list and other information."""

    def __init__(self):
        self.source_dir = os.path.join(ROOT, r"MetaData")
        self.races_list_path = os.path.join(ROOT, r"MetaData\races_list.csv")

    def create_list(self, races=('Tour de France', "Giro d'Italia", 'Vuelta a España')):
        """Create races list.

        :param races: What races to take into account. By default only Grand Tours.
        """
        try:
            with open(self.races_list_path, 'r', encoding=ENCODING) as fr:
                cur_list = pd.read_csv(self.races_list_path)
                fr.close()
        except FileNotFoundError:
            cur_list = pd.DataFrame()

        for item in os.listdir(self.source_dir):
            if os.path.splitext(item)[0] in races:
                cur_race = os.path.splitext(item)[0]
                workbook = pd.read_excel(os.path.join(self.source_dir, item),  # Gets a dict
                                         sheet_name=None, encoding=ENCODING)
                is_multi_stage = 1 if cur_race in MULTI_STAGES else 0
                race_meta_df = pd.DataFrame()
                for year, cur_sheet in workbook.items():  # year is the sheet name; cur_sheet is a dataframe
                    print("----------Examining {} {}----------".format(cur_race, year))
                    has_prologue = 1 if cur_sheet['NUM'][0] == 'P' else 0
                    actual_stage_count = 0
                    for cur_row in cur_sheet.iterrows():
                        if not pd.isna(cur_row[1]['NUM']):  # This is stage information
                            print("    ------Examining stage {}------".format(cur_row[1]['NUM']))
                            num = cur_row[1]['NUM']
                            stage_meta_df = pd.DataFrame({
                                'ID': self._create_id(cur_race, year, cur_row[1]),
                                'Nominal Stage Number': int(num) if self._is_int(num) else num,
                                'Actual Stage Number': self._get_actual_stage_number(has_prologue, cur_row[1]),
                                'Race': cur_race,
                                'Year': year,
                                'Is Multi-Stage': is_multi_stage,
                                'Has Prologue': has_prologue,
                                'Is A Stage': 1 if is_multi_stage else np.nan,
                                'Date': self._get_date(cur_row[1], source='La FlammeRouge'),
                                'Depart': cur_row[1]['DEPART AND ARRIVE'].split('>')[0].strip(),
                                'Arrive': cur_row[1]['DEPART AND ARRIVE'].split('>')[1].strip(),
                                'Length': cur_row[1]['LENGTH'].split('Km')[0].strip(),  # To keep 2 decimal digits
                                'Type': self._get_stage_type(cur_row[1]),
                                'Profile': cur_row[1]['TYPE']  # For now, the profile of a time trial is not clear.
                            }, index=[0])
                            if len(cur_list) == 0 or stage_meta_df['ID'][0] not in cur_list['ID']:
                                cur_list = pd.concat([cur_list, stage_meta_df], ignore_index=True, sort=False)
                            actual_stage_count += 1
                        elif not pd.isna(cur_row[1]['TYPE']):  # This is race information
                            key = cur_row[1]['TYPE']
                            value = cur_row[1]['LENGTH']
                            if key == 'Total distance':
                                value = value.split('Km')[0].strip()
                                race_meta_df.loc.__setitem__((0, key), value)
                                race_meta_df.loc.__setitem__((0, 'Total stages'), actual_stage_count)
                                race_meta_df.loc.__setitem__((0, 'Average distance'),
                                                             str(round(float(value)/actual_stage_count, 2)))
                            else:
                                if self._is_int(value):
                                    value = int(value)
                                race_meta_df.loc.__setitem__((0, key), value)
                        else:
                            pass
                    if is_multi_stage:
                        race_meta_df = pd.DataFrame(dict(dict(race_meta_df), **{
                            'ID': self._create_id(cur_race, year),
                            'Race': cur_race,
                            'Year': year,
                            'Is Multi-Stage': is_multi_stage,
                            'Has Prologue': has_prologue,
                            'Is A Stage': False
                        }))
                        if len(cur_list) == 0 or race_meta_df['ID'][0] not in cur_list['ID']:
                            cur_list = pd.concat([cur_list, race_meta_df], ignore_index=True, sort=False)
                        cur_list.to_csv(self.races_list_path, mode='w', index=False, encoding=ENCODING)
        return

    @staticmethod
    def _create_id(race, year, row_data=None, align=2):
        """
        Create ID for a stage/race, using the NOMINAL stage number.

        Format: abbr_year_code (for a whole race, the last part is set to 'R01', meaning 'Race No.1').

        :param race: The full name of the race.
        :param year: The current year that's being examined.
        :param row_data: The data row being examined.
            When not input it is for the whole race, otherwise for a single stage.
        :param align: The total number of characters for numbering the stage/race.
            By default 2, i.e., stage No.2 will be represented by 02.
            Prologue stick to the same rule, i.e., 0P.
        """
        race_code = RACE_CODES[race]  # Get the abbr code from the full name.
        if type(row_data) == pandas.core.series.Series:
            try:
                number = str(int(row_data['NUM']))  # This is a normal stage if no error
                code = 'S' + '0' * (align - len(number)) + number
            except ValueError:
                code = 'S0P'
        else:
            code = 'R01'
        return race_code + str(year) + code

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
            return abs(num - int(num)) < TOLERANCE
        except ValueError or TypeError:
            return False
