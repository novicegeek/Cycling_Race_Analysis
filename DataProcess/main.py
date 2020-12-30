# -*- coding: utf-8 -*-


import convert_format
import log
import gen_var
import cyclists_list
import races_list
import global_vars
ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


if __name__ == '__main__':
    file_dir_abs = ROOT  # 绝对路径
    file_dir_rel = ""  # 相对路径
    # convert = convert_format.FormatConverter(file_dir_abs)
    # convert.convert_xlsx2csv(race_range=["Giro d'Italia"], year_range=['2017', '2018', '2019'])
    # log.rewrite_log(file_dir_abs + 'Converted_Tidied/tidy_log.txt')
    # tidy = gen_var.DataTidier(file_dir_abs)
    # root_tidy = tidy.tidy_all()
    # extract = gen_var.DataExtracter(file_dir_abs)
    # extract.extract_all(race_range="Giro d'Italia", year_range=list(range(2009, 2017)))
    # extract.extract_all(race_range="Tour de France", year_range=['2018', '2019'])
    # var_gen = gen_var.VarGenerator()
    # var_gen.gen_vars_all(race_range=['Tour de France', 'Vuelta a España'])
    # cl = cyclists_list.CyclistsList()
    # cl.create_list()
    rl = races_list.RacesList()
    rl.create_list()
