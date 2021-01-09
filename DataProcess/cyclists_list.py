# -*- coding: utf-8 -*-
"""
Create from data downloaded yet list of ALL involved cyclists and related information, including:
-full name,
-first name,
-last name,
-nationality (country of origin),
-self-defined cyclist identification code (abbr of nationality + serial number of the same nationality),
-The latest source of update of the cyclist's information,
-team at every individual season.
"""


import json
import os
import pandas as pd
import global_vars
import basics


ENCODING = global_vars.get_value('ENCODING')
NULL_HEADERS = ('Full Name', 'First Name', 'Last Name', 'Country', 'ID')
ROOT = global_vars.get_value('ROOT')


class CyclistsList(object):
    """Create cyclists list and other information."""

    def __init__(self):
        self.cyclists_list_path = os.path.join(ROOT, r"MetaData\cyclists_list.csv")
        self.cyclists_count_path = os.path.join(ROOT, r"MetaData\country_cyclists_count.json")

    def create_list(
        self, races=('Tour de France', "Giro d'Italia", 'Vuelta a España'), source='.csv'
    ):
        """
        Create cyclists list.

        :param races: What races to take into account. By default only Grand Tours.
        :param source: Get information from which source? 
            If ".csv" (default): From "...\\Converted_Raw".
            If ".xlsx": From "...\\Raw".
        :raise ValueError: This error occurs when the "source" parameter is
            neither ".xlsx" nor ".csv.
        """
        if source == '.csv':
            source_dir = 'Converted_Raw'
        elif source == '.xlsx':
            source_dir = 'Raw'
        else:
            raise ValueError("Invalid source type.")

        # Open the existing list document.
        try:
            with open(self.cyclists_list_path, 'r', encoding=ENCODING) as fr:
                cur_list = pd.read_csv(fr)
                fr.close()
            cur_list_cyclists_dict = dict(
                [
                    (
                        '@'.join(list(row[1][['Full Name', 'Country']])), row[0]
                    )
                    for row in cur_list.iterrows()
                ]
            )  # Hash cur_list to accelerate matching. Dict structure: {Full Name@Country: row_index}.
        except FileNotFoundError:
            cur_list = pd.DataFrame()
            cur_list_cyclists_dict = {}
        
        # Open the document recording the number of cyclists from each country.
        try:
            with open(self.cyclists_count_path, 'r', encoding=ENCODING) as fr:
                cur_count = json.load(fr)
                fr.close()
        except FileNotFoundError:
            cur_count = {}
        
        # Walk through every relevant data file.
        source_root = os.path.join(ROOT, source_dir)
        for item in os.listdir(source_root):
            if item in races:  # To avoid the log file; the target item is the race name
                for year in os.listdir(os.path.join(source_root, item)):
                    print("---------- Examining {} {} ----------".format(item, year))
                    cur_path = os.path.join(source_root, item, year)  # In the form of ...\\race_name\\season_year
                    for file in os.listdir(cur_path):
                        if 'FC_GC' in file:
                            with open(os.path.join(cur_path, file), 'r',
                                      encoding=ENCODING) as fr:
                                cur_data = pd.read_csv(fr)
                                fr.close()
                            cur_list, cur_list_cyclists_dict, cur_count = self.add_data_to_list(
                                cur_list, cur_list_cyclists_dict, cur_count,
                                cur_data, year, ', '.join([item, str(year)])
                                )
                            break
                    # Rewrite the cyclists list and record count document after processing every season for a race.
                    basics.write_csv_bom(cur_list, self.cyclists_list_path)
                    with open(self.cyclists_count_path, 'w', encoding=ENCODING) as fw:
                        json.dump(cur_count, fw, ensure_ascii=False)
                        fw.close()
                    
        return

    def add_data_to_list(self, cur_list, cur_cyclists_dict, cur_count, cur_data, year, source):
        """Add or fill up cyclists' data to the final list.

        :param cur_list: The latest version of cyclists' list (as dataframe) before this call.
        :param cur_cyclists_dict: The dictionary generated from cur_list, storing the full names,
            countries and row indexes for fast matching. Structure: {Full Name@Country: row_index}.
        :param cur_count: The counts record BEFORE adding the current cyclist.
        :param cur_data: The data (dataframe) to be scanned in this call.
        :param year: The season year being examined.
        :param source: The latest source of getting the cyclists' data (which race, which season).
        :return: Modified list and record of country-wise counts.
        """
        for row in cur_data.iterrows():
            first_name = row[1]['First Name'].strip()
            last_name = row[1]['Last Name'].strip()
            full_name = ' '.join([first_name, last_name])
            country = row[1]['Country']
            if pd.isna(country):
                print("  Warning: {} skipped due to missing country information.\n"
                      "    Data source: {}".format(full_name, source))
                continue
            team = row[1]['Team']
            team_season_header = '_'.join(['Team', str(year)])
            # print("  Examining {} from {}".format(full_name, country))
            # Match the cyclist with full name and country.
            # If and only if both match, we take it as a valid match.
            # PROBLEM: There could be two cyclists of the same name and from the same country,
            # though the probability is extremely low.
            key = '@'.join([full_name, country])
            index = cur_cyclists_dict.get(key)

            if index is None:  # No match (The cyclist is not in the list)
                index = len(cur_cyclists_dict)
                cur_count, new_id = self._create_id(cur_count, country)
                new_data = pd.DataFrame({
                    'Full Name': full_name,
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Country': country,
                    'ID': new_id,
                    'Source': source,
                    team_season_header: team
                    },  # The fields to be added for a first-time included cyclist.
                    index=[0])
                cur_list = pd.concat([cur_list, new_data], ignore_index=True, sort=False)
                cur_cyclists_dict.update([(key, index)])
                # print("    {} from {} newly appended, with team for {} newly appended"
                #       .format(full_name, country, year))
            else:  # The cyclist is already in the list
                if (team_season_header not in cur_list.columns  # Cyclist checked for the season for the first time
                        or
                        pd.isna(cur_list[team_season_header][index])):
                    cur_list.loc.__setitem__((index, team_season_header), team)
                    cur_list.loc.__setitem__((index, 'Source'), source)
                    # print("    {} from {} already exists, but team assignment for {} newly appended"
                    #       .format(full_name, country, year))
                elif cur_list[team_season_header][index] != team:  # There is a discrepancy between two team records
                    print(
                        "    Warning: A discrepancy occurs between team records for {} from {}, at season {}.\n"
                        "      Old Assignment: {}"
                        "      New Assignment: {}"
                        .format(full_name, country, year, cur_list[team_season_header][index], team)
                        )
                    continue
                else:  # The team record already exists for this season
                    # print("    {} from {} and team assignment for {} already exists".format(full_name, country, year))
                    pass
        return cur_list, cur_cyclists_dict, cur_count
    
    @staticmethod
    def _create_id(cur_count, country, align=4):
        """Create an ID for a newly included cyclist with his/her country known.

        :param cur_count: The counts record BEFORE adding the current cyclist.
        :param country: The 3-character abbreviation of nationality.
        :param align: How many characters for the number's part. By default 4, 
            which means number shorter than 4 digits will be filled by 0s at the head.
            E.g., the 15th cyclist from GBR will get an ID of GBR0004.
        :return: The modified record and the created ID.
        """
        if country in cur_count.keys():
            cur_count[country] += 1  # Other cyclists from the country have been counted.
        else:
            cur_count[country] = 1  # This is the first cyclist from the country.
        count_align = '0' * (align - len(str(cur_count[country]))) + str(cur_count[country])
        new_id = country + count_align
        return cur_count, new_id


class AddMissingCyclists(object):
    """Add those missing in the converted raw General Classification list."""

    def __init__(self):
        self.converted_dir = os.path.join(ROOT, r"Converted_Raw")

    def add_cyclists_to_raw(self, races='multi', seasons='all'):
        """Add cyclists missing in the converted raw General Classification lists, for specified races and seasons.

        :param races: What races to check. Can be 'all', 'multi' (default), 'single',
            or full name of a specific race, or a list of full names of races.
        :param seasons: What seasons to check. Can be 'all', or a specific year or a list of years,
            each of int or str type.
        """
        if type(races) == str:
            if races == 'all':
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
            seasons = [str(year) for year in seasons]
        for race in races:
            for season in seasons:
                print("Checking {} {}".format(race, season))
                cur_dir = os.path.join(self.converted_dir, race, season)
                prim_ref_path, sec_ref_path, gc_path = [''] * 3
                prim_ref_list, sec_ref_list, gc_list = list(map(lambda x: pd.DataFrame(), range(3)))
                # Get S1_SC, S1_SGC and FC_GC file path
                for file_name in os.listdir(cur_dir):
                    if 'S1_SC' in file_name:
                        prim_ref_path = os.path.join(cur_dir, file_name)
                    elif 'S1_SGC' in file_name:
                        sec_ref_path = os.path.join(cur_dir, file_name)
                    elif 'FC_GC' in file_name:
                        gc_path = os.path.join(cur_dir, file_name)
                # Import as dataframes
                if prim_ref_path:
                    with open(prim_ref_path, 'r', encoding=ENCODING) as fr:
                        prim_ref_list = pd.read_csv(fr)
                        fr.close()
                if sec_ref_path:
                    with open(sec_ref_path, 'r', encoding=ENCODING) as fr:
                        sec_ref_list = pd.read_csv(fr)
                        fr.close()
                if gc_path:
                    with open(gc_path, 'r', encoding=ENCODING) as fr:
                        gc_list = pd.read_csv(fr)
                        fr.close()
                # Check if anyone missing in the GC list; skip this iteration if not
                if len(gc_list) == max(len(prim_ref_list), len(sec_ref_list), len(gc_list)):
                    continue
                # If is, set the primary reference list to be the one that is more "complete"
                elif len(prim_ref_list) > len(sec_ref_list):
                    pass
                else:
                    prim_ref_list = sec_ref_list
                # Hash the GC list
                gc_dict = {}
                for row in gc_list.iterrows():
                    try:
                        key = row[1]['First Name'] + ' ' + row[1]['Last Name'] + '@' + row[1]['Country']
                    except TypeError:  # Missing country information (np.nan can't be concatenated with a str)
                        try:
                            key = row[1]['First Name'] + ' ' + row[1]['Last Name']
                        except TypeError:  # An empty row
                            pass
                        else:
                            gc_dict.update({key: row[0]})
                    else:
                        gc_dict.update({key: row[0]})

                total_updates = 0
                for row in prim_ref_list.iterrows():
                    gc_dict, gc_list, update = self._check_cyclist(gc_dict, row[1], gc_list)
                    total_updates += update
                if total_updates and gc_path:
                    basics.write_csv_bom(gc_list, gc_path)
                    print("    GC list for {} {} re-written".format(race, season))
                elif total_updates:  # No GC list has existed before
                    gc_path = os.path.join(cur_dir, r"FC_GC_IRR.csv")
                    basics.write_csv_bom(gc_list, gc_path)
                    print("    GC list for {} {} newly created since none has existed before, "
                          "and named 'FC_GC_IRR.csv'".format(race, season))
        return

    @staticmethod
    def _check_cyclist(gc_dict, row, gc_list,
                       fields=('BIB', 'Last Name', 'First Name', 'Country', 'Team', 'Gender', 'Age')):
        """Check if a single cyclist is in the GC list.

        :param gc_dict: The dictionary generated from GC list as a reference. Structure: {Full Name@Country: row_index}.
            Similarly in gen_var.py.
        :param row: The data row of Series type, extracted from a dataframe.
        :param gc_list: The existing list to append to.
        :return:
            gc_dict-The updated gc_dict,
            gc_list-The updated gc_list,
            update-1 or 0. Whether the gc_list is updated (new cyclist(s) appended) by this call.
        """
        update = 0
        key = row['First Name'] + ' ' + row['Last Name'] + '@' + row['Country']
        key_no_country = row['First Name'] + ' ' + row['Last Name']
        if (gc_dict.get(key) is None) and (gc_dict.get(key_no_country) is None):  # Missing in the current GC list
            index = len(gc_list)
            for field in fields:
                gc_list.loc.__setitem__((index, field), row[field])
            gc_dict.update({key: index})
            print("    {} newly appended".format(key))
            update = 1
        return gc_dict, gc_list, update
