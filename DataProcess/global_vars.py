# -*- coding: utf-8 -*-


global_vars = {}


def set_value(key, value):
    global_vars[key] = value
    return


def get_value(key):
    try:
        return global_vars[key]
    except KeyError:
        return None


set_value('ENCODING', 'utf-8')
set_value('GRAND TOUR', ('Tour de France', "Giro d'Italia", 'Vuelta a España'))
set_value('MULTI-STAGES', ('Tour de France', "Giro d'Italia", 'Vuelta a España',
                           'Tour de Suisse', 'Critérium du Dauphiné', 'Paris-Nice', 'Tirreno-Adriatico'))
set_value('RACES', ('Tour de France', "Giro d'Italia", 'Vuelta a España',
                    'Tour de Suisse', 'Critérium du Dauphiné', 'Paris-Nice', 'Tirreno-Adriatico',
                    'Il Lombardia', 'Liège-Bastogne-Liège', 'Milano-Sanremo', 'Paris-Roubaix', 'Ronde van Vlaanderen'))
set_value('SINGLE-STAGE',
          ('Il Lombardia', 'Liège-Bastogne-Liège', 'Milano-Sanremo', 'Paris-Roubaix', 'Ronde van Vlaanderen'))
set_value('SEASONS', tuple([str(year) for year in range(2009, 2020)]))
set_value('ROOT', r"D:\PKU\LuLab\Master'sThesis\Data")
