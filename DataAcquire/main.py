# -*- coding: utf-8 -*-
"""Initiating module."""


import download


if __name__ == '__main__':
    downloader = download.UCIDownloader()
    sleep = 5
    season_input = list(range(2009, 2020))
    # competition_input = ["Ronde van Vlaanderen / Tour des Flandres",
    #                      "Ronde van Vlaanderen - Tour des Flandres", "Ronde van Vlaanderen-Tour des Flandres",
    #                      "Ronde van Vlaanderen", "Tour des Flandres", "De Ronde van Vlaanderen",
    #                      "Paris-Roubaix", "Paris - Roubaix",
    #                      "Liège-Bastogne-Liège", "Liège - Bastogne - Liège",
    #                      "Il Lombardia", "Giro di Lombardia",
    #                      "Milano-Sanremo", "Milano - Sanremo",
    #                      "Championnats du Monde Route UCI / UCI Road World Championships",
    #                      "Championnats du Monde Route UCI", "UCI Road World Championships"]
    competition_input = ["Tirreno-Adriatico", "Tirreno - Adriatico"]
    # race_input = [' '.join(['Stage', str(i)]) for i in range(1, 18)]
    race_input = 'all'
    # event = ['General classification', 'Stage Classification']

    # while downloader:
    #     print("Please input the year(s) you want to download for.\nFor multiple years, separate with ',':")
    #     season_input = input()
    #     print("You want to download the results in season(s) {},\n"
    #           "press 'Y' to confirm and continue, and 'N' to input again.".format(season_input))
    #     while True:
    #         confirm = input()
    #         if confirm in ['Y', 'y', 'N', 'n']:
    #             break
    #         else:
    #             print("Invalid input. Please input again.")
    #     if confirm in ['Y', 'y']:
    #         season_input = re.split(r',[ ]*', season_input)
    #         break
    #
    # while season_input:
    #     print("Please input the competition(s) you want to download for.\n"
    #           "For multiple competitions, separate with ',':")
    #     competition_input = input()
    #     print("You want to download the results of competition(s) {},\n"
    #           "press 'Y' to confirm and start downloading, and 'N' to input again.".format(competition_input))
    #     while True:
    #         confirm = input()
    #         if confirm in ['Y', 'y', 'N', 'n']:
    #             break
    #         else:
    #             print("Invalid input. Please input again.")
    #     if confirm in ['Y', 'y']:
    #         competition_input = re.split(r',[ ]*', competition_input)
    #         break
    #
    # print("You will start downloading the results for competition(s) {} "
    #       "in season(s) {} in {} seconds. ".format(competition_input, season_input, sleep))

    try:
        downloader.auto_download(seasons_year=season_input, competitions_name=competition_input,
                                 races_name=race_input, time_sleep=sleep, option='exportResultForm')
    except Exception:
        print("Downloading failed.")
    else:
        print("Hooray!")
