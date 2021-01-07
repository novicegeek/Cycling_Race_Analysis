# -*- coding: utf-8 -*-
"""The core downloading module."""


# %%
import copy
import json
import os
import re
import requests
import time
import urllib.parse as parse
import brotli
import bs4
from bs4 import BeautifulSoup as BS
import chardet
import pandas as pd
import global_vars
import path_gen


MAX = 9999
ENCODING = global_vars.get_value('ENCODING')
ROOT = global_vars.get_value('ROOT')


# %%
class UCIDownloader(object):
    """Perform the downloading task."""

    def __init__(self, discipline_id=10, category_id=22, download_dir=ROOT+r"\Raw"):
        """Configure default request settings.

        :param discipline_id: By default 10 (Road Cycling).
        :param category_id: By default 22 (Men Elite).
        :param download_dir: File directory to which all raw data documents will be downloaded.
        """
        self.discipline_id = discipline_id
        self.category_id = category_id
        self.accept = {
            'json': "application/json, text/javascript, */*; q=0.01",
            'xml': "text/html,application/xhtml+xml,application/xml;"
                   "q=0.9,image/webp,image/apng,*/*;"
                   "q=0.8,application/signed-exchange;"
                   "v=b3;"
                   "q=0.9"
        }
        self.accept_encoding = "gzip, deflate, br"
        self.accept_language = "zh-CN,zh;q=0.9,en;q=0.8"
        self.connection = 'keep-alive'
        self.content_type = {
            'with_encoding': "application/x-www-form-urlencoded; charset=UTF-8",
            'without_encoding': "application/x-www-form-urlencoded"
        }
        self.host = "dataride.uci.ch"
        self.origin = "https://dataride.uci.ch"
        self.referer_base = "https://dataride.uci.ch/iframe/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                          "AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/84.0.4147.105 " \
                          "Safari/537.36"
        self.headers = {
            'Accept-Encoding': self.accept_encoding,
            'Accept-Language': self.accept_language,
            'Connection': self.connection,
            'Host': self.host,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': self.user_agent,
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.proxies = {
            'http': "http://127.0.0.1:10809",
            'https': "https://127.0.0.1:10809"
        }
        self.customized_proxies = 'off'  # This attribute indicates whether to use customized proxies or default ones
        self.keys_dict = {
            'Season': {'key_name': 'Year', 'id_name': 'Id'},
            'Competition': {'key_name': 'CompetitionName', 'id_name': 'CompetitionId'},
            'Race': {'key_name': 'RaceName', 'id_name': 'Id'},
            'Event': {'key_name': 'EventName', 'id_name': 'EventId'}
        }
        self.download_dir = download_dir
        return

    def set_proxies(self, proxies):
        self.proxies = proxies
        return

    def customize_proxies(self, option='on'):
        """
        To check and turn on customized proxies (by default).

        "option" can only be "on" or "off".

        :raise ValueError: Error occurs when the "option" parameter is neither "on" nor "off".
        """
        if option.lower() == 'on' or option.lower() == 'off':
            self.customized_proxies = option.lower()
            print("Customized proxies have been turned {}.".format(option))
        else:
            raise ValueError("Invalid parameter")
        return

    def auto_download(self, seasons_year, competitions_name,
                      races_name='all', events_name='all', country_id=0, time_sleep=10,
                      option='exportResultForm', extension='.xlsx'):
        """
        The pivotal adapter for downloading.

        :param seasons_year: Either a list, or a single integer or string.
        :param competitions_name: Either a list or a string.
            E.g., ['Tour de France', "Giro d'Italia"].
        :param races_name: By default download ALL races of an event. Can be set as a list or string.
            E.g., "Stage 6", "Final Result".
        :param events_name: Either a list or a string.
            E.g., "General classification", "Points Classification".
        :param country_id: By default 0 (all countries).
        :param time_sleep: Integer to indicate the time lag between 2 downloading requests.
        :param option: The export option to pass to the function self.export_result()
            and finally to self._get_token_from_page().
            Decides what type of result data to export.
            Only the default option ('exportResultForm') is visible to normal website visitors in the GUI;
            however, 3 additional options ('exportExcelForm', 'exportOdfForm', and 'exportRankingForm')
            can be seen in the source code of the webpage.
        :param extension: The format parameter of saved data documents to pass to the function self.export_result().
        :return: TBD
        """
        # seasons_dict = self.get_seasons_id(seasons_year)
        # all_competitions_dict = {}  # Store competition name-ID pairs for all seasons assigned
        #                             # to avoid multi-layer for-loop or duplicate requesting
        # for season_year, season_id in seasons_dict.items():
        #     competitions_dict = self.get_competitions_id(season_id, competitions_name)
        #     all_competitions_dict.update({season_year: competitions_dict})
        path_generator = path_gen.PathGenerator(self.download_dir)
        for competition in self.gen_all_competitions_dict(seasons_year, competitions_name):
            season_year = list(competition.keys())[0]
            competition_dict = list(competition.values())[0]
            competition_name, competition_id = list(competition_dict.items())[0]
            for event in self.gen_all_events_dict(competition_id, races_name, events_name):
                race_name = event['Race Name']
                date_unix = event['Date']
                race_type = event['Race Type']
                event_dict = event['Event']
                self.export_result(path_generator, season_year, competition_dict,
                                   race_name, date_unix, race_type, event_dict, country_id, option, extension)
                print(
                    "Result for {} ({} season, {}, {}) has been downloaded.\n"
                    "Waiting for the next downloading for {} seconds..."
                    .format(competition_name, season_year, race_name, list(event_dict.keys())[0], time_sleep)
                )
                time.sleep(time_sleep)
        return

    def gen_all_competitions_dict(self, seasons_year, competitions_name):
        """
        A generator to yield competition dictionaries for all specified seasons.

        :return: A generator of single dictionary.
        """
        seasons_list = self.get_seasons_id(seasons_year)
        for season_dict in seasons_list:
            season_year, season_id = list(season_dict.keys())[0], list(season_dict.values())[0]
            competitions_list = self.get_competitions_id(season_id, competitions_name)
            for competition_dict in competitions_list:
                yield {season_year: competition_dict}

    def gen_all_events_dict(self, competition_id, races_name='all', events_name='all'):
        """
        A generator to yield all event dictionaries for a specified competition ID.

        :return: A generator of single dictionary.
        """
        races_info = self.get_races_info(competition_id, races_name)
        for race_dict in races_info:
            race_name, race_id = list(race_dict['Name-ID'].keys())[0], list(race_dict['Name-ID'].values())[0]
            events_list = self.get_events_id(competition_id, race_id, events_name)
            for event_dict in events_list:
                yield {
                    'Race Name': race_name,
                    'Date': race_dict['Date'],
                    'Race Type': race_dict['Race Type'],
                    'Event': event_dict
                }

    def _auto_get_json(self, method, url, query_str=None, form=None, headers=None):
        """
        Automatically get json data from specified url.

        :param method: 'GET' or 'POST'.
        :return: The valid json document.
        :raise Error: An error occurs when the response can't be interpreted as .json document.
        """
        response = self._auto_get_response(method, url, query_str, form, headers)
        try:
            type(response.json())
        except Exception:
            # Try if problem is caused by brotli encoding
            try:
                if response.headers['content-encoding'] == 'br' \
                        and chardet.detect(response.content) != 'ascii':
                    response_str = str(brotli.decompress(response.content), ENCODING)
                else:
                    response_str = ''
                response_json = json.loads(response_str)
            except Exception:
                print("Unknown error: The response can not be interpreted as json normally.")
                raise
        else:
            response_json = response.json()
        if type(response_json) == dict and 'data' in response_json.keys():
            all_list = response_json['data']
        elif type(response_json) == dict or type(response_json) == list:
            all_list = response_json
        else:
            raise TypeError("Unidentified response type.")
        return all_list

    def _auto_get_response(self, method, url, query_str=None, form=None, headers=None):
        """
        Automatically request response from specified url.

        :param method: 'GET' or 'POST'.
        :return: Response as requests.models.Response object.
        """
        if method.upper() == 'GET' or method.upper() == 'POST':
            print("Getting response...")
            try:
                if self.customized_proxies == 'off':
                    response = requests.request(
                        method=method, url=url, params=query_str, data=form, headers=headers
                    )
                else:
                    response = requests.request(
                        method=method, url=url, params=query_str, data=form, headers=headers, proxies=self.proxies
                    )
            except Exception:
                print("Failed to get response.")
                raise
        else:
            raise ValueError('Invalid request method.')
        return response

    def _get_single_id(self, level, reference_list, key, precise=True):
        """
        Extract single id from a reference list, at a specified level.

        :param level: Indicates the ID of which (of season/competition/race/event) to extract.
            Should match one of "Season", "Competition", "Race" and "Event" when capitalized.
        :param reference_list: List(extracted from json) of dictionaries to which to refer the key.
        :param key: Key information (either year or name).
        :param precise: Whether the key should be exactly the same to match the reference (when "True"),
            or match all the reference items that cover the item (when "False").
            E.g., when "key" is "National Championship" and precise=False, all competitions the names of which
            include the key will be extracted.
        :return: For season, competition and event: A LIST of a single key-ID pair in the form a dictionary;
            For race: A LIST containing key-ID pair, date and race type code.
            Returns a null string when no matching result is found.
        :raise ValueError: An error occurs when the no matching key is found in the reference list,
            or the reference list is empty.
        """
        level = level.capitalize()
        if level not in self.keys_dict.keys():
            raise ValueError("Invalid request level: {}.".format(level))
        elif len(reference_list) == 0:
            raise ValueError("Empty reference list: {} '{}'.".format(level, key))
        else:
            key_name = self.keys_dict[level]['key_name']
            id_name = self.keys_dict[level]['id_name']
            if precise and level == 'Race':
                for item in reference_list:
                    if str(item[key_name]).split('-')[0].strip() == str(key):
                        return [self._get_single_race_info(item)]
            elif precise:
                for item in reference_list:
                    if str(item[key_name]) == str(key):
                        return [{key: item[id_name]}]
            else:
                match_list = []
                for item in reference_list:
                    if key in item[key_name]:
                        match_list.append({item[key_name]: item[id_name]} if level != 'Race'
                                          else self._get_single_race_info(item))
                return match_list
        print("{} '{}' not found. Try next one...".format(level, key))
        return ''

    def get_seasons_id(self, seasons_year):
        """
        Get season ID(s) for specified season year(s).

        :param seasons_year: Can either be a list, or a single integer or string.
        :return: LIST of dictionaries of year-ID pairs.
        :raise TypeError: An error occurs when the input season years are in an unrecognizable format.
        """
        all_seasons_list = self._get_seasons_list()
        seasons_list = []
        if type(seasons_year) == int or type(seasons_year) == str:
            seasons_year = [seasons_year]
        elif type(seasons_year) == list:
            pass
        else:
            raise TypeError("Invalid season years.")
        for season_year in seasons_year:
            single_id = self._get_single_id('Season', all_seasons_list, season_year)
            if single_id != '':
                seasons_list += single_id
        return seasons_list

    def _get_seasons_list(self):
        """
        Get the information of multiple seasons in the form of a list.

        :return: A reference list of seasons information for further searching.
        """
        url_base = "https://dataride.uci.ch/iframe/GetRestrictedResultsDisciplineSeasons/"
        query_str = {
            'disciplineId': self.discipline_id
        }
        headers = copy.deepcopy(self.headers)
        headers.update({
            'Accept': self.accept['json'],
            'Referer': ''.join([self.referer_base, 'results/', str(self.discipline_id), '/'])
        })
        all_seasons_list = self._auto_get_json(method='GET', url=url_base, query_str=query_str, headers=headers)
        return all_seasons_list

    def get_competitions_id(self, season_id, competitions_name):
        """
        Get competition ID(s) for specified competition name(s).

        :param season_id: ID of a single game season extracted by function self.get_seasons_id().
        :param competitions_name: Can be a list(multiple competitions) or a string(single competition).
        :return: LIST of dictionaries of competition-ID pairs.
        :raise TypeError: This error occurs when the input competition names are in an unrecognizable format
        """
        all_competitions_list = self._get_competitions_list(season_id, competitions_name)
        competitions_list = []
        if type(competitions_name) == str:
            competitions_name = [competitions_name]
        elif type(competitions_name) == list:
            pass
        else:
            raise TypeError("Invalid competition names.")
        for competition_name in competitions_name:
            single_id = self._get_single_id(
                'Competition', all_competitions_list, competition_name
            )
            if single_id != '':
                competitions_list += single_id
        return competitions_list

    def _get_competitions_list(self, season_id, take=MAX, skip=0, page=1, pagesize=MAX):
        """
        Get the information of multiple competitions of a SINGLE season in the form of a list.

        NOTE: The competition IDs of the same competition in different seasons are DIFFERENT.

        :param season_id: ID of a specific season
        :param take: How many competitions to request? -- Just set to "MAX" before figuring it out
        :param skip: How many competitions to skip before requesting the current batch?
        :param page: Which page to load?
        :param pagesize: How many competitions to load on a single page? -- Just set to "MAX" before figuring it out
        :return: A reference list of competitions information for further searching
        """
        url = "https://dataride.uci.ch/iframe/Competitions/"
        form = {
            'disciplineId': self.discipline_id,
            'take': take,
            'skip': skip,
            'page': page,
            'pageSize': pagesize,
            'sort[0][field]': 'StartDate',
            'sort[0][dir]': 'desc',
            'filter[filters][0][field]': 'RaceTypeId',
            'filter[filters][0][value]': '0',
            'filter[filters][1][field]': 'CategoryId',
            'filter[filters][1][value]': self.category_id,
            'filter[filters][2][field]': 'SeasonId',
            'filter[filters][2][value]': season_id
        }
        headers = copy.deepcopy(self.headers)
        headers.update({
            'Accept': self.accept['json'],
            'Content-Type': self.content_type['with_encoding'],
            'Origin': self.origin,
            'Referer': ''.join([self.referer_base, 'results/', str(self.discipline_id), '/'])
        })
        all_competitions_list = self._auto_get_json(method='POST', url=url, form=form, headers=headers)
        return all_competitions_list

    def get_races_info(self, competition_id, races_name='all'):
        """
        Get dictionaries of name-ID pair, date and race type for specified race name(s).

        :param competition_id: ID of a single competition extracted by function self.get_competitions_id().
        :param races_name: By default get ALL races for the specified competition.
            When customized, this can be a list(multiple competitions) or a string(single competition).
        :return: LIST of dictionaries containing race-ID pair, date and race type.
        :raise TypeError: This error occurs when the input race names are in an unrecognizable format.
        """
        all_races_list = self._get_races_list(competition_id)
        races_info = []
        if races_name == 'all':
            for race in all_races_list:
                races_info.append(self._get_single_race_info(race))
        else:
            if type(races_name) == str:
                races_name = [races_name]
            elif type(races_name) == list:
                pass
            else:
                raise TypeError("Invalid race names.")
            for race_name in races_name:
                single_info = self._get_single_id('Race', all_races_list, race_name)
                if single_info != '':
                    races_info += single_info
        return races_info

    def _get_races_list(self, competition_id, take=MAX, skip=0, page=1, pagesize=MAX):
        """
        Get the information of ALL races for a SINGLE competition in the form of a list.

        :param competition_id: ID of a specific competition.
        :return: A reference list of races information for further searching.
        """
        url = "https://dataride.uci.ch/iframe/Races/"
        form = {
            'disciplineId': self.discipline_id,
            'competitionId': competition_id,
            'take': take,
            'skip': skip,
            'page': page,
            'pageSize': pagesize
        }
        headers = copy.deepcopy(self.headers)
        headers.update({
            'Accept': self.accept['json'],
            'Content-Type': self.content_type['with_encoding'],
            'Origin': self.origin,
            'Referer': ''.join([self.referer_base, 'CompetitionResults/', str(competition_id),
                                '?', parse.urlencode({'disciplineId': self.discipline_id})]),
        })
        all_races_list = self._auto_get_json(method='POST', url=url, form=form, headers=headers)
        return all_races_list

    @staticmethod
    def _get_single_race_info(reference_item):
        """Extract a dictionary containing race-ID pair, date and race type information."""
        race_info = {
            'Name-ID': {reference_item['RaceName']: reference_item['Id']},
            'Date': re.split(r'[()]', reference_item['StartDate'])[1][0:10],
            'Race Type': reference_item['RaceTypeCode']
        }
        return race_info

    def get_events_id(self, competition_id, race_id, events_name='all'):
        """
        Get event ID(s) for for specified event name(s).

        :param race_id: ID of a specific race.
        :param events_name: Can be a list(multiple events) or a string(single event).
        :return: LIST of dictionaries of race-ID pairs.
        :raise TypeError: This error occurs when the input event names are in an unrecognizable format.
        """
        all_events_list = self._get_events_list(competition_id, race_id)
        events_list = []
        if events_name == 'all':
            for event in all_events_list:
                events_list.append({event['EventName']: event['EventId']})
        else:
            if type(events_name) == str:
                events_name = [events_name]
            elif type(events_name) == list:
                pass
            else:
                raise TypeError("Invalid event names.")
            for event_name in events_name:
                single_id = self._get_single_id('Event', all_events_list, event_name)
                if single_id != '':
                    events_list += single_id
        return events_list

    def _get_events_list(self, competition_id, race_id):
        """
        Get the information of ALL events for a SINGLE race in the form of a list.

        :param race_id: ID of a specific race.
        :return: A reference list of events information for further searching.
        """
        url = "https://dataride.uci.ch/iframe/Events/"
        form = {
            'disciplineId': self.discipline_id,
            'raceId': race_id
        }
        headers = copy.deepcopy(self.headers)
        headers.update({
            'Accept': self.accept['json'],
            'Content-Type': self.content_type['with_encoding'],
            'Origin': self.origin,
            'Referer': ''.join([self.referer_base, 'CompetitionResults/', str(competition_id),
                                '?', parse.urlencode({'disciplineId': self.discipline_id})]),
        })
        all_events_list = self._auto_get_json(method='POST', url=url, form=form, headers=headers)
        return all_events_list

    def export_result(self, path_generator, season_year, competition_dict,
                      race_name, date_unix, race_type, event_dict,
                      country_id=0, option='exportResultForm', extension='.xlsx'):
        """
        Core downloader.

        :param path_generator: Class path_gen.PathGenerator object.
        :param date_unix: Time in seconds since the Epoch in Unix.
        :param country_id: By default '0' (download all countries).
        :param option: What type of result data to export.
            Only the default option ('exportResultForm') is visible to normal website visitors in the GUI;
            however, 3 additional options ('exportExcelForm', 'exportOdfForm', and 'exportRankingForm')
            can be seen in the source code of the webpage.
        :param extension: The format of the saved data documents. By default ".xlsx".
        """
        competition_name, competition_id = list(competition_dict.items())[0]
        event_name, event_id = list(event_dict.items())[0]

        session = requests.Session()
        print("Start getting final result page...")
        response_page, session = self._get_result_page(competition_id, event_id, session)
        page_bs = BS(response_page.text, 'html.parser')
        if not option:
            option = 'exportResultForm'
        token = self._get_token_from_page(page_bs, option)

        date_standard = self._unix_to_standard_date(date_unix)

        url = "https://dataride.uci.ch/iframe/ExportResult/"
        form = {
            '__RequestVerificationToken': token,
            'disciplineId': self.discipline_id,
            'eventId': event_id,
            # 'rankingId': '',
            # 'rankingTypeId': '',
            # 'raceTypeId': '',
            # 'categoryId': '',
            # 'disciplineSeasonId': '',
            # 'momentId': '',
            'countryId': country_id,
            'individualName': '',
            'teamName': ''
        }
        headers = copy.deepcopy(self.headers)
        headers.update({
            'Accept': self.accept['xml'],
            'Cache-Control': "max-age=0",
            'Content-Type': self.content_type['without_encoding'],
            'Origin': self.origin,
            'Referer': ''.join([self.referer_base, 'EventResults/', str(event_id), '?',
                                parse.urlencode({
                                    'competitionId': competition_id,
                                    'disciplineId': self.discipline_id
                                })
                                ]),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        print("Start downloading...")
        if self.customized_proxies == 'off':
            response_result = session.post(url=url, data=form, headers=headers)
        else:
            response_result = session.post(url=url, data=form, headers=headers, proxies=self.proxies)
        print("Start Generating file path...")
        [file_dir, file_name, file_path] = path_generator.join_file_path(season_year, date_standard, competition_dict,
                                                                         race_name, event_dict, race_type)
        print("Start writing file...")
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(file_path, 'wb') as fw:  # Write data in the form of binary stream.
            fw.write(response_result.content)
        fw.close()
        if not extension:
            extension = '.xlsx'
        file_path_ext = '.'.join([file_path, extension.lstrip('.')])
        if os.path.exists(file_path_ext):
            os.remove(file_path_ext)
        os.rename(file_path, file_path_ext)

        return

    @staticmethod
    def _unix_to_standard_date(time_unix):
        """ Convert Unix-epoch time to standard 8-digit date string """
        time_convert = time.localtime(int(time_unix))
        year = str(time_convert.tm_year)
        month = str(time_convert.tm_mon)
        month = ''.join(['0', month]) if len(month) == 1 else month
        day = str(time_convert.tm_mday)
        day = ''.join(['0', day]) if len(day) == 1 else day
        date_standard = ''.join([year, month, day])
        return date_standard

    @staticmethod
    def _get_token_from_page(page, option='exportResultForm'):
        """
        Extract token from given page.

        :param page: Can be raw response, string or bs4.BeautifulSoup type.
        :raise ValueError: This error occurs when the page format or the export option cannot be recognized.
        """
        if type(page) == bs4.BeautifulSoup:
            page_bs = page
        elif type(page) == str:
            page_bs = BS(page, 'html.parser')
        elif type(page) == requests.models.Response:
            page_bs = BS(page.text, 'html.parser')
        else:
            raise ValueError("Invalid page format.")

        if option == 'exportExcelForm' or option == 'exportOdfForm':
            action = '/iframe/ExportFile/'
        elif option == 'exportRankingForm':
            action = '/iframe/ExportRanking/'
        elif option == 'exportResultForm':
            action = '/iframe/ExportResult/'
        else:
            raise ValueError("Invalid export option.")
        tag = page_bs.find('form', attrs={'method': 'POST',
                                          'action': action,
                                          'id': option})
        pattern = re.compile('<input.*?value="(.*?)"/>', re.S)
        token = pattern.findall(str(tag))[0]
        return token

    def _get_result_page(self, competition_id, event_id, session=None):
        """
        Get the result page from which to export the final result document.

        :param session: An established request session (for getting verification token.
        :return: Raw response and session
        """
        url_base = ''.join(["https://dataride.uci.ch/iframe/EventResults/", str(event_id)])
        query_str = {
            'competitionId': competition_id,
            'disciplineId': self.discipline_id
        }
        headers = copy.deepcopy(self.headers)  # If not copied, the headers attribute of the class will be changed.
        headers.update({
            'Accept': self.accept['xml'],
            'Cache-Control': "max-age=0",
            'Referer': ''.join([self.referer_base, 'CompetitionResults/', str(competition_id),
                                '?', parse.urlencode({'disciplineId': self.discipline_id})]),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        del(headers['X-Requested-With'])
        if self.customized_proxies == 'off':
            response = session.get(url=url_base, params=query_str, headers=headers)
        else:
            response = session.get(url=url_base, params=query_str, headers=headers, proxies=self.proxies)
        return response, session


class ProCyclingStatsDownloader(object):
    """Download race- and cyclist-related information from https://www.procyclingstats.com"""

    def __init__(self):
        self.url_root = "https://www.procyclingstats.com"
        self.races_list_file_path = os.path.join(ROOT, r"MetaData\races_list.csv")
        self.races_parse_file_path = os.path.join(ROOT, r"Codes\DataAcquire\races_parse.json")
        self.races_parcours_file_path = os.path.join(ROOT, r"MetaData\races_parcours.json")
        self.accept = "text/html,application/xhtml+xml,application/xml;" \
                      "q=0.9,image/avif,image/webp,image/apng,*/*;" \
                      "q=0.8,application/signed-exchange;" \
                      "v=b3;" \
                      "q=0.9"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                          "AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/87.0.4280.88 " \
                          "Safari/537.36"
        self.headers_stage = {
            'Accept': self.accept,
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7",
            'Cache-Control': "max-age=0",
            'Referer': "https://www.procyclingstats.com/races.php",
            'Sec-Ch-Ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'Sec-Ch-Ua-Mobile': "?0",
            'Sec-Fetch-Dest': "document",
            'Sec-Fetch-Site': "same-origin",
            'Sec-Fetch-User': "?1",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': self.user_agent
        }
        self.headers_gc = copy.deepcopy(self.headers_stage)
        self.headers_gc.__delitem__('Cache-Control')
        self.headers_gc.__delitem__('Referer')

    def download_parcours(self, races='all', seasons=tuple(range(2009, 2020)), stages='all'):
        """Download parcours scores from the website, and write them into an individual file.

        :param races: The list/tuple of FULL NAMES of races. By default 'all'.
        :param seasons: Should be a list of str/int. By default tuple of 2009-2019.
        :param stages: What stages to download. Should be a single str/int or a list of str/int.
            Prologue should be as 'P' or 'p'. By default 'all'.
        """
        with open(self.races_parse_file_path, 'r', encoding=ENCODING) as fr:
            races_parse_json = json.load(fr)
            fr.close()
        with open(self.races_list_file_path, 'r', encoding=ENCODING) as fr:
            races_list = pd.read_csv(fr)
            fr.close()
        try:
            with open(self.races_parcours_file_path, 'r', encoding=ENCODING) as fr:
                races_parcours = json.load(fr)
                fr.close()
        except FileNotFoundError:
            races_parcours = {}

        # Transform all 3 variables to be iterable
        if races == 'all':
            pass
        elif type(races) == str:
            races = [races]
        if type(seasons) in [int, str]:
            seasons = [str(seasons)]
        else:
            seasons = [str(season) for season in seasons]
        if stages == 'all':
            pass
        elif type(stages) in [int, str]:
            stages = [str(stages)]
        else:
            stages = [str(stage) for stage in stages]

        try:
            prologue_error_record = [None, None]
            last_write = 0
            for row in races_list.iterrows():
                if races_parcours.get(row[1]['ID']):  # This stage has been added to the .json file
                    continue
                cur_race = row[1]['Race'],  # 奇怪的bug，赋值之后cur_race会变成series类
                cur_race = cur_race[0]
                cur_year = str(row[1]['Year'])
                if [cur_race, cur_year] == prologue_error_record:  # 跳过prologue有问题的年份
                    continue
                cur_stage = row[1]['Nominal Stage Number']
                if pd.isna(cur_stage):  # This is an overall race datum
                    continue
                cur_stage = str(int(float(cur_stage))) if cur_stage != 'P' else cur_stage

                if ((races == 'all' or cur_race in races)
                        and cur_year in seasons
                        and (stages == 'all' or cur_stage in stages)):
                    print("---------- Getting parcours information for {} {}, Stage {} ----------"
                          .format(cur_race, cur_year, cur_stage))
                    cur_race_parse = races_parse_json[cur_race]
                    cur_stage_parse = 'stage-' + cur_stage if cur_stage != 'P' else 'prologue'
                    cur_url = '/'.join([self.url_root, 'race',
                                        cur_race_parse, cur_year, cur_stage_parse,
                                        'result/result'])

                    response = requests.request(method='GET', url=cur_url, headers=self.headers_stage)
                    response_bs = BS(response.text, 'html.parser')
                    info_tag = str(response_bs.find('div', attrs={'class': "res-right"}))

                    pattern_profile_score = re.compile('profile-score">(.*?)</a>', re.S)
                    try:
                        cur_parcours = pattern_profile_score.findall(info_tag)[0]
                    except IndexError:  # Discrepancy on the mark of a prologue, so the returned page is empty
                        prologue_error_record = [cur_race, cur_year]
                        print("Discrepancy on prologue occurs for {} {}".format(cur_race, cur_year))
                    else:
                        races_parcours[row[1]['ID']] = cur_parcours
                        last_write += 1
                    if not last_write % 10:  # 每写入10个新条目覆盖一次.json文件
                        with open(self.races_parcours_file_path, 'w', encoding=ENCODING) as fw:
                            json.dump(races_parcours, fw)
                            fw.close()
        except Exception:
            raise
        finally:
            with open(self.races_parcours_file_path, 'w', encoding=ENCODING) as fw:
                json.dump(races_parcours, fw)
                fw.close()
        return
