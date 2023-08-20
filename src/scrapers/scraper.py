import requests
from bs4 import BeautifulSoup as bs
import logging
from shiny_app.db import init_db, Season, Standing, Team, Round
import json
import string
from pprint import pformat
from datetime import datetime
import crayons

format=f'[%(asctime)s][%(name)s] %(message)s'
f = logging.Formatter(format)
fh = logging.FileHandler(f'log/{__name__}.log', 'w')
fh.setFormatter(f)

class Scraper:
  def __init__(self, test=False) -> None:
    self.logger = logging.getLogger(__name__)
    self.logger.addHandler(fh)
    self.logger.setLevel(logging.DEBUG)
    if test:
      self.session = init_db('sqlite:///tests/allsvenskan.db')
    else:
      self.session = init_db('sqlite:///data/allsvenskan.db')

class WikiScraper(Scraper):
  def __init__(self, test=False) -> None:
    super().__init__(test=test)
    self.url = 'https://sv.wikipedia.org/'

  def input_test(self):
    return input('Does this work? ')

  def deg_to_dec(self, deg):
    _deg, rest = deg.split('°')
    min, rest = rest.split('′')
    sec = rest.split('″')[0]
    return float(_deg) + float(min)/60 + float(sec)/3600
  
  def get_venue(self, team: str):
    """ Try to get the venue of team"""
    venue = {}
    team_ = team.replace(' ', '_')
    url = f'{self.url}wiki/{team_}'
    r = requests.get(url).text
    soup = bs(r, 'html.parser')
    # return soup
    def fuck_flagicons(tag):
      return 'flagicon' not in tag.attrs['class']
    try:
      venue_url = soup.find('th', string='Hemmaarena').find_next_sibling('td').find('a')['href'].lstrip('/')
      r = requests.get(f'{self.url}{venue_url}').text
      soup = bs(r)
      try:
        lat = self.deg_to_dec(soup.find('span', class_='latitude').string)
        lon = self.deg_to_dec(soup.find('span', class_='longitude').string)
        return (lat, lon)
      except:
        return (None, None)
    except:
      try:
        city_url = soup.find('th', string='Hemort').find_next_sibling(fuck_flagicons).find('a')['href'].lstrip('/')
        r = requests.get(f'{self.url}{city_url}').text
        soup = bs(r)
        try:
          lat = self.deg_to_dec(soup.find('span', class_='latitude').string)
          lon = self.deg_to_dec(soup.find('span', class_='longitude').string)
          return (lat, lon)
        except:
          return (None, None)
      except:
        return (None, None)
    

class ESScraper(Scraper):
  """ A class to handle a scraper for everysport.com. """
  def __init__(self, test=False) -> None:
    super().__init__(test=test)
    self.seasons = self.session.query(Season).order_by(Season.year).all()
    self.current_season = self.session.query(Season).filter(Season.year == datetime.today().year).first()
    self.headers = {
      "accept": "*/*",
      "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,sv;q=0.7",
      "content-type": "application/json",
      "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-site",
      "x-api-key": "da2-lwa7k4te7ncp7fhtqoxghuzqp4"
    }
    self.url = 'https://api.www.everysport.com/graphql'
  
  def check_team(self, team):
    """ Check if team exists in database. If not, add it. """
    t = self.session.query(Team).filter_by(name=team).first()
    if t is None:
      self.session.add(Team(name=team))
      self.session.commit()
      team_id = self.check_team(team)
    else:
      team_id = t.id
    return team_id

  def get_standings_for_round(self, _round: int=None) -> list:
    """ Get standings for a round.
      
        Keyword arguments:
        _round -- the number of the round. Default is None, and raises a Value Error.
        add -- if True adds the results as a new round to the database (default=False)
    """
    if _round is None:
      raise ValueError('You must specify a round.')
    season = self.current_season
    payload = string.Template("{\"operationName\":\"GetSeriesStandings\",\"variables\":{\"id\":\"$season_id\",\"input\":{\"type\":\"TOTAL\",\"round\":$_round}},\"query\":\"query GetSeriesStandings($$id: ID!, $$input: StandingsFilterInput) {\\n  series: seriesStandings(id: $$id, input: $$input) {\\n    id\\n    name\\n    startDate\\n    endDate\\n    groups {\\n      labels {\\n        type\\n        name\\n        __typename\\n      }\\n      standings {\\n        position\\n        lineThicknessBelow\\n        team {\\n          id\\n          name\\n          __typename\\n        }\\n        stats {\\n          name\\n          value\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"}")
    payload = payload.substitute(season_id=season.id, _round=_round)
    r = requests.post(self.url, data=payload, headers=self.headers)
    data = r.json()
    return data['data']['series']['groups'][0]['standings']
  
  def add_standings(self, _r: int):
    '''Get the data for the selected season and round. Check for each team if the round is already in the database, if not add it.'''

    _round = self.session.query(Round).filter(Round.season_id == self.current_season.id).filter(Round._round == _r).first()
    if _round is None:
      # New round, add it to season
      _round = Round(_round=_r, final=True)
      self.current_season.get_final_round().final = False
      self.current_season.rounds.append(_round)
    data = self.get_standings_for_round(_r)
    for t in data:
      team = self.session.query(Team).filter(Team.name == t['team']['name']).first()
      standing = self.session.query(Standing).filter(Standing.round_id == _round.id, Standing.team_id == team.id).first()
      games = int(t['stats'][0]['value'])
      if standing is None or standing.games < games:
      # if team.name not in _round.teams():
        d = dict(
            round_id = _round.id,
            # team_id = session.query(Team).filter(Team.name == t['team']['name']).first().id,
            position = int(t['position']),
            games = games,
            wins = int(t['stats'][1]['value']),
            draws = int(t['stats'][2]['value']),
            losses = int(t['stats'][3]['value']),
            gf = int(t['stats'][4]['value']),
            ga = int(t['stats'][5]['value']),
            points = int(t['stats'][7]['value']),
        )
        standing = Standing(**d)
        standing.team = team
        # print(f'Adding {standing}')
        _round.standings.append(standing)
      else:
        self.logger.info(f'Keeping {standing}')
        continue
    self.session.add(self.current_season)
    # self.logger.info(_round.as_table())
    self.session.commit()

  def get_games_for_round(self, year, _round: str) -> dict:
    ''' Get results for <_round> in <season>'''   
    payload = string.Template("{\"operationName\":\"Fetchgames\",\"variables\":{\"input\":{\"seriesId\":\"$season_id\",\"round\":$round}},\"query\":\"query Fetchgames($$input: GamesFilterInput) {\\n  result: games(input: $$input) {\\n    metadata {\\n      totalCount\\n      count\\n      offset\\n      limit\\n      __typename\\n    }\\n    games {\\n      id\\n      status\\n      finishStatus\\n      startDate\\n      sport {\\n        id\\n        name\\n        slug\\n        __typename\\n      }\\n      homeTeam {\\n        name\\n        shortName\\n        __typename\\n      }\\n      awayTeam {\\n        name\\n        shortName\\n        __typename\\n      }\\n      score {\\n        homeTeam\\n        awayTeam\\n        __typename\\n      }\\n      series {\\n        id\\n        name\\n        year\\n        division {\\n          id\\n          countryCode\\n          class\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"}")
    payload = payload.substitute(season_id=self.current_season.id, round=_round)
    # self.logger.info(payload)
    r = requests.post(self.url, data=payload, headers=self.headers)
    data = r.json()
    return data['data']
      # self.logger.info(f"{game['homeTeam']['name']} {game['score']['homeTeam']} - {game['score']['awayTeam']} {game['awayTeam']['name']}")



if __name__ == '__main__':
  ...
  # s = Scraper()
  # if sys.argv[1] == 'standings':
  #   s.get_standings()
  # elif sys.argv[1] == 'games':
  # season = s.session.query(Season).filter(Season.year == 1961).first()
  # s.logger.info(pformat(s.get_standings_for_round(season, 1)))
  # s.get_games_for_round(s.current_season, _round=8)