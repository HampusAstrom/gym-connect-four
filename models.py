from sqlalchemy import Boolean, Column, Integer, String, JSON, Float

from database import Base


class StudentGame(Base):
    __tablename__ = "student_games"

    #id = Column(Integer, primary_key=True, index=True)
    stil_id = Column(String, primary_key=True, unique=True, index=True)
    running = Column(Boolean)
    state = Column('data', JSON)
    played = Column(Integer)
    won = Column(Integer)
    lost = Column(Integer)
    streak = Column(Integer)
    total_reward = Column(Float)
