import pytest
import pandas as pd
from src.models import Season, Round, Game, Standing, Team, init_db
from src.util.getters import get_teams_for_season
from sqlalchemy import func
import matplotlib.pyplot as plt
#import plotly.express as px

@pytest.fixture
def session():
    return init_db('sqlite:///tests/allsvenskan.db')

def test_round(session):
    season = session.query(Season).filter(Season.year == 2017).first()
    _round = season.get_round(18)
    assert _round._round == 18
    with pytest.raises(IndexError):
        _round = season.get_round(38)
      
def test_final_round(session):
    seasons = session.query(Season).order_by(Season.year).all()
    for season in seasons:
      num_rounds = session.query(func.max(Round._round)).filter(Round.season_id == season.id).scalar()
      final_round = session.query(Round).filter(Round.season == season).filter(Round._round == num_rounds).first()

def test_team(session):
    seasons = session.query(Season).order_by(Season.year).all()
    data = {}
    teams = session.query(Team).all()
    for team in teams:
        data[team.name] = [team.progression_for_season(season) for season in seasons]
    df = pd.DataFrame(data=data, index=[int(season.year[-4:]) for season in seasons])
    with open('data/progressions.json', 'w') as f:
        df.to_json(f, force_ascii=False)
    # df = pd.read_json('data/progressions.json')
    # df.sort_values(axis=1, by=2023, inplace=True, ascending=False)
    # selected_teams = slice(0, 4)
    # selected_seasons = slice(*df.index.get_indexer((2008, 2023)))
    # print('\n')
    # print(df.index[-1])
    # df.iloc[selected_seasons, selected_teams].plot()
    # plt.show()
    
def test_season_progression(session):
    season = session.query(Season).filter(Season.year==2017).first()
    print(season.as_df())

def test_diffs(session):

    # seasons = session.query(Season).order_by(Season.year).all()
    # data = {'leader': [], 'runner-up': [], 'diff': []}
    # teams = session.query(Team).all()
    # i = 0
    # runner_up_p = 0
    # for season in seasons:
    #     _round = season.get_final_round()
    #     for standing in sorted(_round.standings, key=lambda x: x.team.progression_for_season(season), reverse=True)[:2]:
    #         if i % 2 == 0:
    #             data['leader'].append(standing.team.name)
    #             leader_p = standing.team.progression_for_season(season)
    #         else:
    #             data['runner-up'].append(standing.team.name)
    #             runner_up_p = standing.team.progression_for_season(season)
    #             data['diff'].append(leader_p-runner_up_p)
    #         i += 1
    # df = pd.DataFrame(data, index=[int(season.year[-4:]) for season in seasons])
    # print('\n')
    # with open('data/diffs.json', 'w') as f:
    #     df.to_json(f, force_ascii=False)

    df = pd.read_json('data/diffs.json')
    # selected_seasons = slice(*df.index.get_indexer((2008, 2023)))
    df.sort_values(by='diff', inplace=True, ascending=False)
    # print('\n')
    # print(df.iloc[selected_seasons, :])
    df.plot.density()
    plt.show()

def test_venues(session):
    data = {'lat_mean': [], 'lon_mean': [], 'lat_max': [], 'lon_max': [], 'lat_min': [], 'lon_min': [], 'lat_maxteam': [], 'lon_maxteam': [], 'lat_minteam': [], 'lon_minteam': []}
    df = pd.read_json('data/venues.json')
    seasons = session.query(Season).order_by(Season.year).all()
    # print(df.loc[lambda df: df['lat'] == season_df.apply(min)['lat']].index.values[0])
    for season in seasons: 
        _round = season.rounds[0]
        teams = [standing.team.name for standing in _round.standings]
        season_df = df.filter(teams, axis=0)
        for key in data.keys():
            col, func = key.split('_')
            if 'team' in func:
                func = func[:3]
                data[key].append(df.loc[lambda df: df[col] == season_df.apply(func)[col]].index.values[0])
            else:
                data[key].append(season_df.apply(func)[col])
    
    
    col, func = 'lat_max'.split('_')
    print(season_df.apply(func)[col])
    df2 = pd.DataFrame(data, index=[season.year for season in seasons])
    
    with open('data/coords.json', 'w') as f:
        df2.to_json(f, force_ascii=False)

def test_coords():
    df = pd.read_json('data/venues.json')
    df2 = pd.read_json('data/coords.json')

    fig = px.scatter_mapbox(df2, lat='lat_mean', lon='lon_mean', size='lat_mean', size_max=10, hover_name=df2.index, hover_data={'teams': [get_teams_for_season(s) for s in df2.index]})
    fig.update_layout(mapbox_style='open-street-map')
    fig.show()

    # Get lat from max_lon
    # ax.scatter(df2.lon_max.max(), df.loc[lambda df: df.lon == df2.lon_max.max()].lat[0], zorder=1, alpha=1, c='r', s=10)