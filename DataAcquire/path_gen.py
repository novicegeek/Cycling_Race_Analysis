# -*- coding: utf-8 -*-
"""Generate complete file path from given information."""


import json
import re


class PathGenerator(object):

    def __init__(self, dir_base):
        self._load_code_json()
        self.dir_base = dir_base

    def _load_code_json(self):
        with open("competition_codes.json", 'r', encoding='utf-8') as fr:
            self.competition_codes = json.load(fr)
        fr.close()
        # with open("race_codes.json", 'r') as fr:
        #     self.race_codes = json.load(fr)
        # fr.close()
        # with open("event_codes.json", 'r') as fr:
        #     self.event_codes = json.load(fr)
        # fr.close()
        # with open("race_type_codes.json", 'r') as fr:
        #     self.race_type_codes = json.load(fr)
        # fr.close()
        return

    def join_file_path(self, season_year, date, competition_dict, race_name, event_dict, race_type, mode='full'):
        """
        Generate file path WITHOUT the extension.

        Note that season year and date may NOT match (the beginning of each season year is not that of a calendar year).

        :param date: Should be in standard 8-digit string format.
        :param race_type: Only abbreviation.
        :param mode: "full" or "abbr". Determines whether to use full name or abbreviation
            for competition name in file DIRECTORY.
        :return: LIST: [file directory, file name, joint file path].
        """
        file_dir = self._gen_file_dir(season_year, competition_dict, mode)
        file_name = self._gen_file_name(date, competition_dict, race_name, event_dict, race_type)
        return [file_dir, file_name, '/'.join([file_dir, file_name])]

    def _gen_file_dir(self, season_year, competition_dict, mode):
        """Path format: self.download_dir/competition(full)/season_year/filename."""
        competition_full = list(competition_dict.keys())[0]
        if mode == 'full':
            if '/' in competition_full:
                competition_full = competition_full.split('/')[0].strip()
            file_dir = '/'.join([self.dir_base, competition_full, str(season_year)])
        else:
            try:
                file_dir = '/'.join([self.dir_base, self.competition_codes[competition_full], str(season_year)])
            except KeyError:
                file_dir = '/'.join([self.dir_base, self._get_abbr('Competition', competition_full), str(season_year)])
                print("Abnormal competition name occur: {}. Abbreviated as: {}.".format(competition_full, file_dir))
        return file_dir

    def _gen_file_name(self, date, competition_dict, race_name, event_dict, race_type_abbr):
        """
        Generate file name WITHOUT the extension.

        :param date: Standard 8-digit string.
        :return: The combined file name, EXCLUDING the directory and extension.
            File name format: date_competition(abbr)_race(stage)_event_race type.
        """
        competition_full = list(competition_dict.keys())[0]
        event_name = list(event_dict.keys())[0]
        try:
            competition_abbr = self.competition_codes[competition_full]
        except KeyError:
            competition_abbr = self._get_abbr('Competition', competition_full)
            print("Abnormal competition name occur: {}. Abbreviated as: {}.".format(
                competition_full, competition_abbr)
            )
        finally:
            race_abbr = self._get_abbr('Race', race_name)
            event_abbr = self._get_abbr('Event', event_name)
            file_name = '_'.join([date, competition_abbr, race_abbr, event_abbr, race_type_abbr])
            return file_name

    @staticmethod
    def _get_abbr(level, name):
        """
        Get abbreviation for competition/race/event name.

        :param level: "Competition", "Race", "Event" or "Race Type".
        :return: The abbreviation.
        """
        if level == 'Race' and 'Stage' in name:
            abbr = 'S' + re.split(r'[ -]', name)[1]
        else:
            abbr = ''.join([part[0].upper() for part in re.split(r'[ -]', name)])
        return abbr
