from src.models import init_db, Season

session = init_db('sqlite:///tests/allsvenskan.db')

def get_teams_for_season(year:int=None):
    if year is None:
        raise ValueError('Please provide a year.')
    else:
        season = session.query(Season).filter(Season.year == year).first()
        _round = season.get_final_round()
        return _round.teams()

def get_season(year):
    return session.query(Season).filter(Season.year == year).first()

if __name__ == '__main__':
    get_teams_for_season()