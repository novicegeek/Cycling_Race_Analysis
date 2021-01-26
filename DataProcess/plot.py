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


def plot_races_hist():
    meta_dir = os.path.join(ROOT, r"MetaData")
    races_list_path = os.path.join(meta_dir, r"races_list.csv")
    races_list = pd.read_csv(races_list_path)

    plain_races = races_list[races_list['Profile'] == 'Plain']
    medium_races = races_list[races_list['Profile'] == 'Medium']
    high_races = races_list[races_list['Profile'] == 'High']
    itt_races = races_list[races_list['Type'] == 'ITT']

    plt.figure()
    plt.hist(itt_races['Winner Avg Speed'])
    plt.xlabel('Winner Average Speed (kph)')
    plt.ylabel('Number of Races')
    plt.title('Histogram of Winner Average Speed for ITT Races')
    plt.show()

    for row in itt_races.iterrows():
        if row[1]['Winner Avg Speed'] < 38 or row[1]['Winner Avg Speed'] > 54:
            print("Row {} -- ID: {}, length: {}, winner average speed: {}"
                  .format(row[0], row[1]['ID'], row[1]['Length'], row[1]['Winner Avg Speed']))

    return


if __name__ == '__main__':
    # plot_races()
    pass
