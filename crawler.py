# %%
# import urllib3
# import urllib.request as request
# import random
import urllib.parse as parse
import requests
import bs4
from bs4 import BeautifulSoup as BS
import re
import chardet
import brotli
import json
import copy
import time
import os
MAX = 9999


# %%
class UCIDownloader(object):
    """ Automatically download race results from https://uci.org. """

    def __init__(self, discipline_id=10, category_id=22, download_dir=r"D:/PKU/LuLab/Masters'Thesis/Data/Raw"):
        """
        Configure default request settings
        :param discipline_id: By default 10 (Road Cycling)
        :param category_id: By default 22 (Men Elite)
        :param download_dir: File directory to which all raw data documents will be downloaded
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
        To check and turn on customized proxies (by default)
        "option" can only be "on" or "off"
        """
        if option.lower() == 'on' or option.lower() == 'off':
            self.customized_proxies = option.lower()
            print("Customized proxies have been turned {}.".format(option))
        else:
            raise ValueError("Invalid parameter")
        return

    def auto_download(self, seasons_year, competitions_name,
                      races_name='all', events_name='all', country_id=0, time_sleep=10):
        """
        The pivotal adapter for downloading
        :param seasons_year: Either a list, or a single integer or string
        :param competitions_name: Either a list or a string
        :param races_name: By default download ALL races of an event. Can be set as a list or string
        :param events_name: Either a list or a string
        :param country_id: By default 0 (all countries)
        :param time_sleep: Integer to indicate the time lag between 2 downloading requests
        :return: TBD
        """
        # seasons_dict = self.get_seasons_id(seasons_year)
        # all_competitions_dict = {}  # Store competition name-ID pairs for all seasons assigned
        #                             # to avoid multi-layer for-loop or duplicate requesting
        # for season_year, season_id in seasons_dict.items():
        #     competitions_dict = self.get_competitions_id(season_id, competitions_name)
        #     all_competitions_dict.update({season_year: competitions_dict})
        path_generator = PathGenerator(self.download_dir)
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
                                   race_name, date_unix, race_type, event_dict, country_id)
                print("Result for {} ({} season, {}, {}) has been downloaded.\n"
                      "Waiting for the next downloading for {} seconds...". format(
                    competition_name, season_year, race_name, list(event_dict.keys())[0], time_sleep)
                )
                time.sleep(time_sleep)

    def gen_all_competitions_dict(self, seasons_year, competitions_name):
        """
        A generator to yield competition dictionaries for all specified seasons
        :return: A generator of single dictionary
        """
        seasons_list = self.get_seasons_id(seasons_year)
        for season_dict in seasons_list:
            season_year, season_id = list(season_dict.keys())[0], list(season_dict.values())[0]
            competitions_list = self.get_competitions_id(season_id, competitions_name)
            for competition_dict in competitions_list:
                yield {season_year: competition_dict}

    def gen_all_events_dict(self, competition_id, races_name='all', events_name='all'):
        """
        A generator to yield all event dictionaries for a specified competition ID
        :return: A generator of single dictionary
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
        Automatically get json data from specified url
        :param method: 'GET' or 'POST'
        :return: The valid json document
        """
        response = self._auto_get_response(method, url, query_str, form, headers)
        try:
            type(response.json())
        except Exception:
            # Try if problem is caused by brotli encoding
            try:
                if response.headers['content-encoding'] == 'br' \
                        and chardet.detect(response.content) != 'ascii':
                    response_str = str(brotli.decompress(response.content), 'utf-8')
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
        Automatically request response from specified url
        :param method: 'GET' or 'POST'
        :return: Response as requests.models.Response object
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
        Extract single id from a reference list, at a specified level
        :param level: Indicates the ID of which (of season/competition/race/event) to extract.
        Should match one of "Season", "Competition", "Race" and "Event" when capitalized
        :param reference_list: List(extracted from json) of dictionaries to which to refer the key
        :param key: Key information (either year or name)
        :param precise: Whether the key should be exactly the same to match the reference (when "True"),
        or match all the reference items that cover the item (when "False").
        E.g., when "key" is "National Championship" and precise=False, all competitions the names of which
        include the key will be extracted.
        :return: For season, competition and event: A LIST of a single key-ID pair in the form a dictionary
        For race: A LIST containing key-ID pair, date and race type code
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
        raise KeyError("{} '{}' not found.".format(level, key))

    def get_seasons_id(self, seasons_year):
        """
        Get season ID(s) for specified season year(s)
        :param seasons_year: Can either be a list, or a single integer or string.
        :return: LIST of dictionaries of year-ID pairs
        """
        all_seasons_list = self._get_seasons_list()
        if type(seasons_year) == int or type(seasons_year) == str:
            seasons_list = self._get_single_id('Season', all_seasons_list, seasons_year)
        elif type(seasons_year) == list:
            seasons_list = []
            for season_year in seasons_year:
                seasons_list += self._get_single_id('Season', all_seasons_list, season_year)
        else:
            raise TypeError("Invalid season years.")
        return seasons_list

    def _get_seasons_list(self):
        """
        Get the information of multiple seasons in the form of a list
        :return: A reference list of seasons information for further searching
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
        Get competition ID(s) for specified competition name(s)
        :param season_id: ID of a single game season extracted by function self.get_seasons_id()
        :param competitions_name: Can be a list(multiple competitions) or a string(single competition)
        :return: LIST of dictionaries of competition-ID pairs
        """
        all_competitions_list = self._get_competitions_list(season_id, competitions_name)
        if type(competitions_name) == str:
            competitions_list = self._get_single_id(
                'Competition', all_competitions_list, competitions_name
            )
        elif type(competitions_name) == list:
            competitions_list = []
            for competition_name in competitions_name:
                competitions_list += self._get_single_id(
                    'Competition', all_competitions_list, competition_name
                )
        else:
            raise TypeError("Invalid competition names.")
        return competitions_list

    def _get_competitions_list(self, season_id, take=MAX, skip=0, page=1, pagesize=MAX):
        """
        Get the information of multiple competitions of a SINGLE season in the form of a list
        NOTE: The competition IDs of the same competition in different seasons are DIFFERENT
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
        Get dictionaries of name-ID pair, date and race type for specified race name(s)
        :param competition_id: ID of a single competition extracted by function self.get_competitions_id()
        :param races_name: By default get ALL races for the specified competition.
        When customized, this can be a list(multiple competitions) or a string(single competition)
        :return: LIST of dictionaries containing race-ID pair, date and race type
        """
        all_races_list = self._get_races_list(competition_id)
        if races_name == 'all':
            races_info = []
            for race in all_races_list:
                races_info.append(self._get_single_race_info(race))
        elif type(races_name) == str:
            races_info = self._get_single_id('Race', all_races_list, races_name)
        elif type(races_name) == list:
            races_info = []
            for race_name in races_name:
                races_info += self._get_single_id('Race', all_races_list, race_name)
        else:
            raise TypeError("Invalid race names.")
        return races_info

    def _get_races_list(self, competition_id, take=MAX, skip=0, page=1, pagesize=MAX):
        """
        Get the information of ALL races for a SINGLE competition in the form of a list
        :param competition_id: ID of a specific competition
        :return: A reference list of races information for further searching
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
        """
        Extract a dictionary containing race-ID pair, date and race type information
        """
        race_info = {
            'Name-ID': {reference_item['RaceName']: reference_item['Id']},
            'Date': re.split(r'[()]', reference_item['StartDate'])[1][0:10],
            'Race Type': reference_item['RaceTypeCode']
        }
        return race_info

    def get_events_id(self, competition_id, race_id, events_name='all'):
        """
        Get event ID(s) for for specified event name(s)
        :param race_id: ID of a specific race
        :param events_name: Can be a list(multiple events) or a string(single event)
        :return: LIST of dictionaries of race-ID pairs
        """
        all_events_list = self._get_events_list(competition_id, race_id)
        if events_name == 'all':
            events_list = []
            for event in all_events_list:
                events_list.append({event['EventName']: event['EventId']})
        elif type(events_name) == str:
            events_list = self._get_single_id('Event', all_events_list, events_name)
        elif type(events_name) == list:
            events_list = []
            for event in all_events_list:
                if event['EventName'] in events_name:
                    events_list.append({event['EventName']: event['EventId']})
        else:
            raise TypeError("Invalid event names.")
        return events_list

    def _get_events_list(self, competition_id, race_id):
        """
        Get the information of ALL events for a SINGLE race in the form of a list
        :param race_id: ID of a specific race
        :return: A reference list of events information for further searching
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
                      race_name, date_unix, race_type, event_dict, country_id=0):
        """
        Core downloader
        :param path_generator: Class PathGenerator object
        :param date_unix: Time in seconds since the Epoch in Unix
        :param country_id: By default '0' (download all countries)
        :return:
        """
        competition_name, competition_id = list(competition_dict.items())[0]
        event_name, event_id = list(event_dict.items())[0]

        session = requests.Session()
        response_page, session = self._get_result_page(competition_id, event_id, session)
        page_BS = BS(response_page.text, 'html.parser')
        token = self._get_token_from_page(page_BS)

        date_standard = self._unix_to_standard_date(date_unix)

        url = "https://dataride.uci.ch/iframe/ExportResult/"
        form = {
            '__RequestVerificationToken': token,
            'disciplineId': self.discipline_id,
            'eventId': event_id,
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

        [file_dir, file_name, file_path] = path_generator.join_file_path(season_year, date_standard, competition_dict,
                                                                         race_name, event_dict, race_type)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(file_path, 'wb') as fw:
            fw.write(response_result.content)
        fw.close()
        file_path_ext = '.'.join([file_path, 'xlsx'])
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
    def _get_token_from_page(page):
        """
        Extract token from given page
        :param page: Can be raw response, string or bs4.BeautifulSoup type
        """
        if type(page) == bs4.BeautifulSoup:
            page_BS = page
        elif type(page) == str:
            page_BS = BS(page, 'html.parser')
        elif type(page) == requests.models.Response:
            page_BS = BS(page.text, 'html.parser')
        else:
            raise ValueError("Invalid page format.")
        tag = page_BS.find('form', attrs={'method': 'POST',
                                          'action': '/iframe/ExportResult/',
                                          'id': 'exportResultForm'})
        pattern = re.compile('<input.*?value="(.*?)"/>', re.S)
        token = pattern.findall(str(tag))[0]
        return token

    def _get_result_page(self, competition_id, event_id, session=None):
        """
        Get the result page from which to export the final result document
        :session: An established request session (for getting verification token
        :return: Raw response and session
        """
        url_base = ''.join(["https://dataride.uci.ch/iframe/EventResults/", str(event_id)])
        query_str = {
            'competitionId': competition_id,
            'disciplineId': self.discipline_id
        }
        headers = copy.deepcopy(self.headers)
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


class PathGenerator(object):
    """ Generate complete file path from given information """

    def __init__(self, dir_base):
        self._load_code_json()
        self.dir_base = dir_base

    def _load_code_json(self):
        with open("competition_codes.txt", 'r', encoding='utf-8') as fr:
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
        Generate file path WITHOUT the extension
        Note that season year and date may NOT match (the beginning of each season year is not that of a calendar year)
        :param date: Should be in standard 8-digit string format
        :param race_type: Only abbreviation
        :param mode: "full" or "abbr". Determines whether to use full name or abbreviation
                     for competition name in file DIRECTORY.
        :return: LIST: [file directory, file name, joint file path]
        """
        file_dir = self._gen_file_dir(season_year, competition_dict, mode)
        file_name = self._gen_file_name(date, competition_dict, race_name, event_dict, race_type)
        return [file_dir, file_name, '/'.join([file_dir, file_name])]

    def _gen_file_dir(self, season_year, competition_dict, mode):
        """ Path format: self.download_dir/competition(full)/season_year/filename """
        competition_full = list(competition_dict.keys())[0]
        if mode == 'full':
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
        Generate file name WITHOUT the extension
        File name format: date_competition(abbr)_race(stage)_event_race type
        :param date: Standard 8-digit string
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
        Get abbreviation for competition/race/event name
        :param level: "Competition", "Race", "Event" or "Race Type"
        :return:
        """
        if level == 'Race' and 'Stage' in name:
            abbr = 'S' + re.split(r'[ -]', name)[1]
        else:
            abbr = ''.join([part[0].upper() for part in re.split(r'[ ]', name)])
        return abbr


# %%
if __name__ == '__main__':
    downloader = UCIDownloader()
    sleep = 10
    season_input = [2018, 2017, 2016]
    competition_input = ['Tour de France', "Giro d'Italia"]
    race_input = [' '.join(['Stage', str(i)]) for i in range(1, 14)]
    # event = ['General classification', 'Stage Classification']

    # while downloader:
    #     print("Please input the year(s) you want to download for.\nFor multiple years, separate with ',':")
    #     season_input = input()
    #     print("You want to download the results in season(s) {},\n"
    #           "press 'Y' to confirm and continue, and 'N' to input again.".format(season_input))
    #     while True:
    #         confirm = input()
    #         if confirm == ('Y' or 'y' or 'N' or 'n'):
    #             break
    #         else:
    #             print("Invalid input. Please input again.")
    #     if confirm == ('Y' or 'y'):
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
    #         if confirm == ('Y' or 'y' or 'N' or 'n'):
    #             break
    #         else:
    #             print("Invalid input. Please input again.")
    #     if confirm == ('Y' or 'y'):
    #         competition_input = re.split(r',[ ]*', competition_input)
    #         break
    #
    # print("You will start downloading the results for competition(s) {} "
    #       "in season(s) {} in {} seconds. ".format(competition_input, season_input, sleep))

    try:
        downloader.auto_download(seasons_year=[2019], competitions_name="La Vuelta ciclista a España",
                                 races_name=race_input, time_sleep=sleep)
    except Exception:
        print("Downloading failed.")
    else:
        print("Hooray!")
