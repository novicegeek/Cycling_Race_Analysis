"""For temporary mostly single-time operations."""


import json
import os
import numpy as np
import pandas as pd
import basics
import convert_format
import cyclists_list
import global_vars


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


def tmp_add_missing_to_list():
    tba_list = (
        ("Vuelta a España", 2017),
        ("Critérium du Dauphiné", 2017)
    )
    add_missing = cyclists_list.AddMissingCyclists()
    for item in tba_list:
        add_missing.add_cyclists_to_raw(races=item[0], seasons=item[1])
    return


def tmp_add_missing_race_info():
    races_list_path = os.path.join(ROOT, r"MetaData\races_list.csv")
    with open(races_list_path, 'r', encoding=ENCODING) as fr:
        races_list = pd.read_csv(fr)
        fr.close()
    with open("competition_codes_rev.json", 'r', encoding=ENCODING) as fr:
        race_codes_rev = json.load(fr)
        fr.close()
    tidy_dir = os.path.join(ROOT, 'Converted_Tidied')

    last_write = 0
    for row in races_list.iterrows():
        if row[1]['Is Multi-Stage'] == 1 and row[1]['Is A Stage'] == 0:
            race_id = row[1]['ID']
            print("Adding to {}...".format(race_id))
            race_length = row[1]['Total distance']
            races_list.loc.__setitem__((row[0], 'Length'), race_length)
            races_list.loc.__setitem__((row[0], 'Type'), 'OVR')

            race, season = race_codes_rev[race_id[:3]], str(row[1]['Year'])
            source_path = os.path.join(tidy_dir, race, season, race_id + '_IRR_GC.csv')
            with open(source_path, 'r', encoding=ENCODING) as fr:
                source_data = pd.read_csv(fr)
                fr.close()

            # 相应地，Tidy的数据里Avg Speed (kph)和Avg Speed Rel to Median都是空的，要补充写入
            time_secs = list(source_data['Total Time'])
            avgs_kph = pd.Series([race_length / ind_time * 3600 for ind_time in time_secs])
            winner_avg = avgs_kph[0]
            median_avg = np.median(avgs_kph[:avgs_kph.count()])
            for row_source in source_data.iterrows():
                cur_avg = avgs_kph[row_source[0]]
                if not pd.isna(cur_avg):
                    source_data.loc.__setitem__((row_source[0], 'Avg Speed (kph)'), cur_avg)
                    source_data.loc.__setitem__((row_source[0], 'Avg Speed Rel to Median'), cur_avg / median_avg)
            basics.write_csv_bom(source_data, source_path)

            races_list.loc.__setitem__((row[0], 'Winner Avg Speed'), winner_avg)
            races_list.loc.__setitem__((row[0], 'Median Avg Speed'), median_avg)
            last_write += 1
            if not last_write % 10:
                basics.write_csv_bom(races_list, races_list_path)

    basics.write_csv_bom(races_list, races_list_path)
    return


def tmp_clear_confound_records():
    records_dir = os.path.join(ROOT, r"Cyclist_Records")
    for file_name in os.listdir(records_dir):
        file_path = os.path.join(records_dir, file_name)
        with open(file_path, 'r', encoding=ENCODING) as fr:
            cur_js = json.load(fr)
            fr.close()
        for key, value in cur_js.items():
            if key[-3:] == 'R01':
                try:
                    del(cur_js[key]['SC'])
                except KeyError:
                    pass
        with open(file_path, 'w', encoding=ENCODING) as fw:
            json.dump(cur_js, fw)
            fw.close()
    return


def tmp_convert_raw():
    tbc_list = (
        ("Giro d'Italia", (2009, 2011, 2013, 2016)),
        ("Vuelta a España", (2009, 2010, 2011, 2017)),
        ("Critérium du Dauphiné", (2011, 2015, 2017)),
        ("Tour de Suisse", 2015),
        ("Tirreno-Adriatico", 2015),
        ("Il Lombardia", (2018, 2019))
    )

    convert = convert_format.FormatConverter()
    for item in tbc_list:
        convert.convert_xlsx2csv(races=item[0], seasons=item[1], ignore_log=True)
    return


# tmp_add_missing_race_info()
# tmp_add_missing_to_list()
# tmp_clear_confound_records()
# tmp_convert_raw()
