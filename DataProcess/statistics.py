import os
import pandas as pd
import statsmodels.api as sma
import global_vars


ROOT = global_vars.get_value('ROOT')


def lm():
    meta_dir = os.path.join(ROOT, r"MetaData")
    races_list_path = os.path.join(meta_dir, r"races_list.csv")
    races_list = pd.read_csv(races_list_path)

    speeds = races_list[races_list['Type'] == 'IRR']['Winner Avg Speed']
    speeds = speeds[speeds.notna()]
    lengths = races_list['Length'][speeds.index]
    lengths = sma.add_constant(lengths)
    slm = sma.OLS(speeds, lengths).fit()

    print(slm.summary())

    return


if __name__ == '__main__':
    # lm()
    pass
