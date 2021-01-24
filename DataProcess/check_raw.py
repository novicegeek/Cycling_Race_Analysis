"""Checking the problems in the raw data files downloaded from UCI."""


import json
import os
import numpy as np
import pandas as pd
import basics
import global_vars


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


class RawChecker(object):

    def __init__(self):
        self.raw_dir = os.path.join(ROOT, r"Raw")
        self.types_set = {'SC', 'SGC', 'GC'}

    def check_raw(self):
        """To check the raw data and shoot out problems."""
        check_count, log_count = 0, 1
        # Create an output log handle
        check_raw_log_path = os.path.join(self.raw_dir, r"check_raw_log_1.txt")
        while os.path.exists(check_raw_log_path):
            log_count += 1
            check_raw_log_path = os.path.join(self.raw_dir, r"check_raw_log_" + str(log_count) + '.txt')
        fw = open(check_raw_log_path, 'w', encoding=ENCODING)

        # Scan all raw files
        for item in os.listdir(self.raw_dir):
            if os.path.isdir(os.path.join(self.raw_dir, item)):
                for season in os.listdir(os.path.join(self.raw_dir, item)):
                    print("Checking {} {}...".format(item, season))
                    cur_dir = os.path.join(self.raw_dir, item, season)
                    file_paths = basics.get_file_list(cur_dir, extension='.xlsx')
                    for file_path in file_paths:
                        file_name = os.path.split(file_path)[1]
                        file_name_split = os.path.splitext(file_name)[0].split('_')
                        if file_name_split[2] == 'FC' and file_name_split[3] != 'GC':
                            continue
                        if file_name_split[3] not in self.types_set:
                            continue
                        if file_name_split[4] == 'TTT':
                            continue
                        fw.write("---- Checking {}... ----\n".format(file_name))
                        cur_data = pd.read_excel(file_path)
                        for row in cur_data.iterrows():
                            if row[0] == 0:
                                if (type(row[1]['Result']) == str and '+' in row[1]['Result']) \
                                        or pd.isna(row[1]['Result']) \
                                        or basics.time2sec(row[1]['Result']) < 300:
                                    fw.write("    Abnormal winner time: {}\n".format(row[1]['Result']))
                            if pd.isna(row[1]['Country']):
                                fw.write("    Cyclist {}: Country missing\n".format(row[0]))
                            # if pd.isna(row[1]['Team']):
                            #     fw.write("    Cyclist {}: Team missing\n".format(row[0]))
                            if pd.isna(row[1]['Age']):
                                fw.write("    Cyclist {}: Age missing\n".format(row[0]))
                            if not pd.isna(row[1]['IRM']):
                                if not pd.isna(row[1]['Rank']):
                                    fw.write(
                                        "    Cyclist {}: {} with non-empty ranking\n".format(row[0], row[1]['IRM'])
                                    )
                            elif not pd.isna(row[1]['Rank']) and pd.isna(row[1]['Result']):
                                fw.write("    Cyclist {}: Non-empty ranking without time\n".format(row[0]))
                        check_count += 1
                        if not check_count % 2500:
                            log_count += 1
                            fw.close()
                            check_raw_log_path = os.path.join(self.raw_dir, r"check_raw_log_" + str(log_count) + '.txt')
                            fw = open(check_raw_log_path, 'w', encoding=ENCODING)
        fw.close()
        return

    def count_stages(self):
        count_stages_log_path = os.path.join(self.raw_dir, r"count_stages_log.txt")
        fw = open(count_stages_log_path, 'w', encoding=ENCODING)

        for item in os.listdir(self.raw_dir):
            if os.path.isdir(os.path.join(self.raw_dir, item)):
                for season in os.listdir(os.path.join(self.raw_dir, item)):
                    stages_set = set()
                    cur_dir = os.path.join(self.raw_dir, item, season)
                    file_paths = basics.get_file_list(cur_dir, extension='.xlsx')
                    for file_path in file_paths:
                        file_name = os.path.split(file_path)[1]
                        stages_set.add(os.path.splitext(file_name)[0].split('_')[2])
                    stages_str = ', '.join([stage for stage in stages_set])
                    fw.write("{} {} records: {}\n".format(item, season, stages_str))

        fw.close()
        return
