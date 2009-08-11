from sqlalchemy import Table, Column, MetaData, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from . import db

Base = declarative_base()
class Bookmark(Base):
    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    genome = Column(String(100))
    sequence = Column(String(255))
    start = Column(Integer)
    stop = Column(Integer)
    orientation = Column(Integer)

    def __init__(self, name, genome, sequence, start, stop, orientation):
        self.name = name
        self.genome = genome
        self.sequence = sequence
        self.start = start
        self.stop = stop
        self.orientation = orientation

    def __repr__(self):
        return "<Bookmark(%d, '%s', ...)>" % (self.id, self.name)

def create_a_bunch(session):
    session.add_all([
        Bookmark('a small bit', 'example', 'seq', 10, 500, +1),
        Bookmark('entire seq', 'example', 'seq', 0, 50000, +1)
        ])

def add_bookmark(name, genome, sequence, start, stop, orientation,
                 session=None):
    commit = False
    if session is None:
        commit = True
        session = db.get_session()
    b = Bookmark(name, genome, sequence, start, stop, orientation)
    session.add(b)

    if commit:
        session.commit()
    
def get_all(session, genome):
    q = session.query(Bookmark).filter(Bookmark.genome == genome).\
        order_by(Bookmark.name)

    return list(q)
