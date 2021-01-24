import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import global_vars


ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


def plot_races():
    meta_dir = os.path.join(ROOT, r"MetaData")
    races_list_path = os.path.join(meta_dir, r"races_list.csv")
    with open(races_list_path, 'r', encoding=ENCODING) as fr:
        races_list = pd.read_csv(fr)
        fr.close()
    winner_avg = np.asarray(races_list['Winner Avg Speed'])
    median_avg = np.asarray(races_list['Median Avg Speed'])

    plt.figure()

    plt.scatter(median_avg, winner_avg, label='scatter')
    # plt.plot(median_avg, winner_avg, label='scatter')

    plt.xlabel('Median Average Speed (kph)')
    plt.ylabel('Winner Average Speed (kph)')

    plt.title('Winner VS. Average Speed in KPH')

    plt.legend()

    plt.show()

    return


if __name__ == '__main__':
    # plot_races()
