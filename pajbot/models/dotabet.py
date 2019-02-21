import logging
import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

from pajbot.managers.db import Base

log = logging.getLogger('pajbot')


class DotaBetGame(Base):
    __tablename__ = 'tb_dotabet_game'

    id = Column(Integer, primary_key=True)
    internal_id = Column(DateTime, default=datetime.datetime.now())
    outcome = Column(Enum('win', 'loss', name='win_or_loss'), nullable=False)
    points_change = Column(Integer, nullable=False)
    win_betters = Column(Integer, nullable=False)
    loss_betters = Column(Integer, nullable=False)

    def __init__(self, outcome, points_change, win_betters, loss_betters):
        self.outcome = outcome
        self.points_change = points_change
        self.win_betters = win_betters
        self.loss_betters = loss_betters


class DotaBetBet(Base):
    __tablename__ = 'tb_dotabet_bet'

    id = Column(Integer, primary_key=True)
    game_time = Column(DateTime, default=datetime.datetime.now())
    user_id = Column(Integer, nullable=False, index=True)
    outcome = Column(Enum('win', 'loss', name='win_or_loss'), nullable=False)
    points = Column(Integer, nullable=False)
    profit = Column(Integer, nullable=False)

    def __init__(self, user_id, outcome, points, profit):
        self.user_id = user_id
        self.outcome = outcome
        self.points = points
        self.profit = profit
