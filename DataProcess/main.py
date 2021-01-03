# -*- coding: utf-8 -*-


import convert_format
import cyclists_list
import gen_var
import global_vars
import races_list


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


if __name__ == '__main__':
    # convert = convert_format.FormatConverter(ROOT)
    # convert.convert_xlsx2csv()
    tidy = gen_var.DataTidier()
    tidy.tidy_all()
    # extract = gen_var.DataExtracter(file_dir_abs)
    # extract.extract_all(race_range="Giro d'Italia", year_range=list(range(2009, 2017)))
    # extract.extract_all(race_range="Tour de France", year_range=['2018', '2019'])
    # var_gen = gen_var.VarGenerator()
    # var_gen.gen_vars_all(race_range=['Tour de France', 'Vuelta a España'])
    # cl = cyclists_list.CyclistsList()
    # cl.create_list()
    # rl = races_list.RacesList()
    # rl.create_list()
