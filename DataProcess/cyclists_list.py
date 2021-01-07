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
ROOT = global_vars.get_value('ROOT')
NULL_HEADERS = ('Full Name', 'First Name', 'Last Name', 'Country', 'ID')


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
        except FileNotFoundError:
            cur_list = pd.DataFrame()
        
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
                            cur_list, cur_count = self.add_data_to_list(
                                cur_list, cur_count, cur_data, year, ', '.join([item, str(year)])
                                )
                            break
                    # Rewrite the cyclists list and record count document after processing every season for a race.
                    basics.write_csv_bom(cur_list, self.cyclists_list_path)
                    with open(self.cyclists_count_path, 'w', encoding=ENCODING) as fw:
                        json.dump(cur_count, fw, ensure_ascii=False)
                        fw.close()
                    
        return

    def add_data_to_list(self, cur_list, cur_count, cur_data, year, source):
        """Add or fill up cyclists' data to the final list.

        :param cur_list: The latest version of cyclists' list (as dataframe) before this call.
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
            print("  Examining {} from {}".format(full_name, country))
            # Match the cyclist with full name and country.
            # If and only if both match, we take it as a valid match.
            # PROBLEM: There could be two cyclists of the same name and from the same country,
            # though the probability is extremely low.
            try:
                match = cur_list[
                    (cur_list['Full Name'] == full_name)
                    &
                    (cur_list['Country'] == country)
                    ]
            except KeyError:  # An empty dataframe
                match = pd.DataFrame()
            if len(match) == 0:  # The cyclist is not in the list
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
            else:  # The cyclist is already in the list
                index = list(match.index)[0]
                if (team_season_header not in cur_list.columns  # Cyclist checked for the season for the first time
                        or
                        pd.isna(cur_list[team_season_header][index])):
                    cur_list.loc.__setitem__((index, team_season_header), team)
                    cur_list.loc.__setitem__((index, 'Source'), source)
                elif cur_list[team_season_header][index] != team:  # There is a discrepancy between two team records
                    print(
                        "  Warning: A discrepancy occurs between team records for {} from {}, at season {}."
                        "    Old Assignment: {}"
                        "    New Assignment: {}"
                        .format(full_name, country, year, cur_list[team_season_header][index], team)
                        )
                    continue
                else:  # The team record already exists for this season
                    pass
        return cur_list, cur_count
    
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
