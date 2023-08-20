from scrapers.scraper import Scraper
from src.models import init_db, Season, Round, Standing, Team

def scrape_all_rounds():
    ''' Scrape everysport.com for all rounds of all seasons and add them to the database '''
    session = init_db('sqlite:///data/allsvenskan.db')

    scraper = Scraper()
    seasons = session.query(Season).all()
    scraper.session = session
    for season in seasons:
        for r in range(1, 31):
            try:
                standings = scraper.get_standings_for_round(season, r)
            except TypeError:
                continue
            _round = Round()
            for s in standings:
                standing = Standing(
                    # team_id = scraper.check_team(standings[0]['team']['name']),
                    team = session.query(Team).filter(Team.name == s['team']['name']).first(),
                    position = s['position'],
                    games = s['stats'][0]['value'],
                    wins = s['stats'][1]['value'],
                    draws = s['stats'][2]['value'],
                    losses = s['stats'][3]['value'],
                    gf = s['stats'][4]['value'],
                    ga = s['stats'][5]['value'],
                    points = s['stats'][7]['value'],
                )
                _round._round = standing.games
                _round.standings.append(standing)
                season.rounds.append(_round)
                session.add(season)
            session.commit()