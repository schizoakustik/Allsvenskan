import pytest
from src.models import Season, Round, Game, Standing, Team, init_db
from src.util.getters import get_teams_for_season
from src.util.formulas import Point, haversine
from itertools import permutations, starmap
import pandas as pd
import numpy as np

@pytest.fixture
def session():
    return init_db('sqlite:///tests/allsvenskan.db')

def test_get_teams_for_season():
    print(get_teams_for_season(1994))

def test_distance(session):
    seasons = session.query(Season).order_by(Season.year).all()
    teams = session.query(Team).all()
    venues = pd.read_json('data/venues.json')
    data = []
    
    for season in seasons:
        season_teams = get_teams_for_season(season.year)
        dists = []
        for team in teams:
            if team.name not in season_teams:
                # print(f'{team.name} not in season')
                dists.append(np.nan)
                # print(f'{team.name} {dist}')
            else:
                dist = 0.0
                for t2 in season_teams:
                    if team.name == t2:
                        pass
                    else: 
                        dist += haversine(Point(*venues.loc[team.name].to_list()), (Point(*venues.loc[t2].to_list()))) * 2
                # print(f'{team.name} {dist}')
                dists.append(dist)
        data.append(dists)
    df = pd.DataFrame(data, index=[season.year for season in seasons], columns=[team.name for team in teams])
    # print(df)
    with open('data/distances.json', 'w') as f:
        df.to_json(f)

def test_dist_json():
    df = pd.read_json('data/distances.json')
    df.plot.bar()