# -*- coding: utf-8 -*-


import convert_format
import cyclists_list
import gen_var
import global_vars
import merge_records
import races_list


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


if __name__ == '__main__':
    # convert = convert_format.FormatConverter(ROOT)
    # convert.convert_xlsx2csv()

    # cl = cyclists_list.CyclistsList()
    # cl.create_list(global_vars.get_value('SINGLE-STAGE'))

    # rl = races_list.RacesList()
    # rl.create_list(races_list.MULTI_STAGES)

    # add_cyclists = cyclists_list.AddMissingCyclists()
    # add_cyclists.add_cyclists_to_raw(races='single')

    # tidy = gen_var.DataTidier()
    # tidy.tidy_all()

    # extract = gen_var.DataExtracter()
    # extract.extract_all(races='all')

    merge_records = merge_records.MergeByCyclistSplitBySeason()
    merge_records.create()

    # var_gen = gen_var.VarGenerator()
    # var_gen.gen_vars_all(race_range=['Tour de France', 'Vuelta a España'])

    pass
