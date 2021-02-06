# -*- coding: utf-8 -*-


import check_raw
import convert_format
import cyclists_list
import gen_var
import global_vars
import merge_records
import races_list


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


if __name__ == '__main__':
    # check_raw = check_raw.RawChecker()
    # check_raw.check_raw()
    # check_raw.count_stages()

    # convert = convert_format.FormatConverter(ROOT)
    # convert.convert_xlsx2csv()

    # cl = cyclists_list.CyclistsList()
    # cl.create_list(global_vars.get_value('SINGLE-STAGE'))

    # rl = races_list.RacesList()
    # rl.create_list(races='all', seasons='all', overwrite=False)

    # add_cyclists = cyclists_list.AddMissingCyclists()
    # add_cyclists.add_cyclists_to_raw(races='single')

    # tidy = gen_var.DataTidier()
    # tidy.tidy_all(races='single', seasons='all', types=['SC', 'GC'],
    #               ignore_log=True, write_record_dict=True, prior_check=False)

    # extract = gen_var.DataExtracter()
    # extract.extract_all(races='all')

    # merge_records = merge_records.MergeByCyclistSplitBySeason()
    # merge_records.create()

    # meta_gen = merge_records.GenerateMetaByCyclistSplitBySeason()
    # meta_gen.gen_meta(seasons=2019, in_place=False)

    # meta_gen = merge_records.GenerateCyclistMeta()
    # meta_gen.gen_meta(races_filter='single', merge=True)
    # meta_gen.merge_meta(races_filter='all')

    # var_gen = gen_var.VarGenerator()
    # var_gen.gen_vars_all(race_range=['Tour de France', 'Vuelta a España'])
    pass


# TODO: 将赛段加入列时，没有考虑到FC成绩里有时候会存在Sprint Classification，也会被缩写为SC加入到列表中造成一些干扰
# TODO: 时间差似乎不是一个好的变量，因为它不是定比变量，只是一个定距变量；用完成时相对于冠军的比值可能更好（本质上是平均速度之比）
# TODO:
#   1.tidied文件：time_lag保留；新增列：1）总用时（s）；2）平均速度（kph）；3）与冠军均速之比（时间反比）；
#     4）与中位数均速之比
#   2.extracted文件：加入tidied中新加入的几列，注意排除混淆的FC_SC（实际上是sprint classification）
#   3.races list：加入单日赛
#   4.merged文件：把其他多日赛和单日赛都加入
# TODO-试验计划：
#   1.从tidied文件开始，命名改为race id_stage type_result type的形式
#   2.从tidied文件开始直接生成merged文件，跳过extracted步骤，且为每一个cyclist生成一个记录其所有完赛结果的json，
#     配合对所有赛事生成一个start list的json文件（只生成FC_GC的名单，即总名单，不管单赛段）
