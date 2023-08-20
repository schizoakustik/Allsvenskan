import pytest
import pandas as pd
from shiny_app.db import Season, Round, Game, Standing, Team, init_db
from scrapers.scraper import ESScraper, WikiScraper
import json
import pprint

@pytest.fixture
def session():
    return init_db('sqlite:///tests/allsvenskan.db')

def test_esscraper(session):
    s = ESScraper(test=True)
    # season = session.query(Season).filter(Season.year == 2023).first()
    assert s.current_season.year == '2023'
    with pytest.raises(ValueError):
        s.get_standings_for_round()
       

def test_round_out_of_bounds(session):
    scraper = ESScraper(test=True)
    # season = session.query(Season).filter(Season.year == 2023).first()
    # scraper.session = session
    scraper.get_standings_for_round(_round=12)
    # with pytest.raises(TypeError): 
    #     scraper.get_standings_for_round(season, 27)

def test_current_season(session):
    s = ESScraper()
    assert s.current_season.year == '2023'

def test_add_standings(session):
    _r = 13
    session = session
    scraper = ESScraper(test=True)
    scraper.add_standings(_r)
    # data = scraper.get_standings_for_round(_r)
    # s = session.query(Season).filter(Season.year == 2023).first()
    # r = Round(season_id = s.id, _round=_r)
    # s.rounds.append(r)
    # for t in data:
    #     d = dict(
    #         round_id = r.id,
    #         # team_id = session.query(Team).filter(Team.name == t['team']['name']).first().id,
    #         position = int(t['position']),
    #         games = int(t['stats'][0]['value']),
    #         wins = int(t['stats'][1]['value']),
    #         draws = int(t['stats'][2]['value']),
    #         losses = int(t['stats'][3]['value']),
    #         gf = int(t['stats'][4]['value']),
    #         ga = int(t['stats'][5]['value']),
    #         points = int(t['stats'][7]['value']),
    #     )
    #     standing = Standing(**d)
    #     standing.team = session.query(Team).filter(Team.name == t['team']['name']).first()
    #     r.standings.append(standing)
    # print(r.as_table())
        

def test_wikiscraper(session):
    # scraper = WikiScraper()
    # venues = {'lat': [], 'lon': []}
    # teams = session.query(Team).all()
    # print('\n')
    # for team in teams:
    #     for k, v in zip(venues.keys(), scraper.get_venue(team.name)):
    #         if v is not None:
    #             venues[k].append(v)
    #         else:
    #             venues[k].append(float(input(f'{k} for {team.name}: ')))
    # df = pd.DataFrame(venues, index=[team.name for team in teams])
    
    # with open('data/venues.json', 'w') as f:
    #     df.to_json(f, force_ascii=False)
    df = pd.read_json('data/venues.json')
    print((df['lat'].mean(), df['lon'].mean()))