from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, create_engine, select
from sqlalchemy.orm import relationship, sessionmaker, DeclarativeBase, mapped_column
from sqlalchemy.ext.hybrid import hybrid_method
import numpy as np
import pandas as pd

class Base(DeclarativeBase):
    pass

class Season(Base):
    ''' A full season of Rounds. 

            Attributes:
            -----------
                id : int 
                    The id for the season. The same as the season id at everysport.com for scraping reasons.
                year : str 
                    The year of the season. The type is string because of the seasons that were played over two calendar years.
                rounds : list 
                    A relationship that collects all rounds associated with the season.

            Methods:
            --------
                get_round(n: int):
                    Returns the round with number *n*. Raises IndexError if no such round exists.

                get_final_round():
                    Returns the round currently marked as the final round. Is the season is finished, it is the last round. If the season is in play, it is the latest season with at least one standing.

                as_df():
                    Returns the season as a Pandas DataFrame.

                table():
                    Prints the season's current standings to console.

    '''

    __tablename__ = 'season'
    id = mapped_column(Integer, primary_key=True)
    year = Column(String)
    rounds = relationship('Round', back_populates='season')

    def get_round(self, n):
        """ Returns the round with number *n*. Raises IndexError if no such round exists. """
        for _round in self.rounds:
            if _round._round == n:
                return _round
        raise IndexError()

    def get_final_round(self):
        """ Returns the round currently marked as the final round. Is the season is finished, it is the last round. If the season is in play, it is the latest season with at least one standing. """
        for _round in self.rounds:
            if _round.final:
                return _round

    def as_df(self):
        """ Returns the season as a pandas DataFrame."""
        data = {}
        teams = self.get_final_round().teams()
        for team in teams:
            data[team] = []
        for r in self.rounds:
            for standing in r.standings:
                try:
                    data[standing.team.name].append(standing.points)
                except:
                    pass
        df = pd.DataFrame(data, columns=teams, index=[r._round for r in self.rounds])
        df.sort_values(axis=1, by=self.get_final_round()._round, inplace=True, ascending=False)
        return df

    def table(self, round=None):
        """ Prints the season's current standings to console. 
                Arguments:
                    round (int, optional):
                        Specify the round to show table for. Default is None, which shows the latest round.
        """
        if round is None:
            print(self.get_final_round().as_table())
        else:
            print(self.get_round(round).as_table())

    def __repr__(self) -> str:
        return f'<Season(year={self.year}, id=({self.id}))>'
    
class Round(Base):
    ''' A round with standings and games. '''

    __tablename__ = 'round'
    id = mapped_column(Integer, primary_key=True)
    _round = Column(Integer)
    final = Column(Boolean, default=False) # Is it the final round of the season?
    season_id = mapped_column(Integer, ForeignKey('season.id'))
    season = relationship('Season', back_populates='rounds')
    standings = relationship('Standing', back_populates='_round')
    games = relationship('Game', back_populates='_round')

    def teams(self):
        """ Return a list of strings representing the team names"""
        return [s.team.name for s in self.standings]

    def teams_as_rows(self):
        """ Return a list of the teams as full rows"""
        return [s.team for s in self.standings]

    def as_table(self):
        output = f'*** Säsong {self.season.year} Omgång {self._round} ***'
        output += f'\n{"Plats":_<{8}}{"Lag":_<{20}}{"M":_>{5}}{"V":_>{5}}{"O":_>{5}}{"F":_>{5}}{"GM":_>{5}}{"IM":_>{5}}{"+/-":_>{5}}{"P":_>{5}}'
        output += ''.join([s.as_row() for s in sorted(self.standings, key=lambda x: x.position)])
        return output
    
    def __repr__(self) -> str:
        return f'Säsong {self.season.year} Omgång {self._round}'

class Standing(Base):
    ''' One row per team after each matchday. '''

    __tablename__ = 'standing'
    id = mapped_column(Integer, primary_key=True)
    round_id = mapped_column(Integer, ForeignKey('round.id'))
    team_id = mapped_column(Integer, ForeignKey('team.id'))
    _round = relationship('Round', back_populates='standings')
    team = relationship("Team", back_populates="standings")
    position = Column(Integer)
    games = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    gf = Column(Integer)
    ga = Column(Integer)
    points = Column(Integer)

    def as_row(self):
        if self.games > 0:
            try:
                return f'\n{self.position:^8}{self.team.name:<20}{self.games:>5}{self.wins:>5}{self.draws:>5}{self.losses:>5}{self.gf:>5}{self.ga:>5}{self.gf-self.ga:>5}{self.points:>5}'
            except Exception as e:
                return(str(e))
        else: return False

    def __repr__(self):
        return f'\n[{self._round.season.year}:{self._round._round}] [{self.team.name}] [{self.games}]'


class Game(Base):
    ''' A game '''
    __tablename__ = 'game'
    id = mapped_column(Integer, primary_key=True)
    round_id = mapped_column(Integer, ForeignKey('round.id'))
    _round = relationship('Round', back_populates='games')
    date = Column(DateTime)
    finished = Column(Boolean)
    home_team_id = mapped_column(Integer, ForeignKey('team.id'))
    away_team_id = mapped_column(Integer, ForeignKey('team.id'))
    home_team = relationship('Team', foreign_keys=home_team_id)
    away_team = relationship('Team', foreign_keys=away_team_id)
    home_team_score = Column(Integer)
    away_team_score = Column(Integer)

    def __repr__(self) -> str:
        return f'<Game {self.date} Matchday {self.matchday.matchday}> {self.home_team.name} {self.home_team_score} - {self.away_team_score} {self.away_team.name}'

class Team(Base):
    ''' A team '''
    __tablename__ = 'team'
    id = mapped_column(Integer, primary_key=True)
    name = Column(String)
    # city = Column(String)
    # venue = Column(String)
    # lat = Column(String)
    # lon = Column(String)
    # home_games = relationship('Game', back_populates='home_team')
    # away_games = relationship('Game', back_populates='away_team')
    standings = relationship('Standing', back_populates='team')
    primary_color = Column(String)
    secondary_color = Column(String)

    def total_points(self):
        """ Sum all points from all seasons for team. SHOULD NOT BE USED as the convention is to count all wins as three points, which is stupid. Maybe one day someone will see reason, and this method will be here waiting."""

        return sum([standing.points for standing in self.standings if standing._round.final])
    
    def total_points_3p_win(self):
        """ Sum all points from all seasons with wins pre-1990 also as three point games. """

        return sum([(standing.wins*3 + standing.draws) for standing in self.standings if standing._round.final])

    def progression(self):
        stmt = f'''
        SELECT year, SUM(points) 
            OVER (
                ORDER BY year 
                ROWS UNBOUNDED PRECEDING
                ) 
            FROM standing 
            INNER JOIN season on season.id = season_id 
            WHERE team_id={self.id} 
            ORDER BY year ASC;'''
        
        return np.cumsum([(standing.wins*3 + standing.draws) for standing in sorted(self.standings, key=lambda x: x._round.season.year) if standing._round.final])

    def progression_for_season(self, season):
        try:
            return np.cumsum([
            (standing.wins*3+standing.draws) for standing in sorted([
                standing for standing in self.standings 
                if standing._round.season.year <= season.year], 
                key=lambda x: x._round.season.year) if standing._round.final])[-1]
        except IndexError:
            # No games this season
            return 0
        
    def plot(self, season_range):
        data = {}
        for standing in sorted([standing for standing in self.standings if standing._round.final], key=lambda x: x._round.season.year):
            for year in season_range:
                data['x'] = year
                data['y'] = np.cumsum(standing.wins*3 + standing.draws)[-1]
        return data

    def __repr__(self) -> str:
        return f'<Team(name="{self.name}">'

def init_db(eng='sqlite:///::memory::'):
    # engine = create_engine('sqlite:///test_maraton.db')
    engine = create_engine(eng)
    session = sessionmaker()
    session.configure(bind=engine)
    Base.metadata.create_all(engine)

    return session()