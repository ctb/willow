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
    color = Column(String(100))

    def __init__(self, name, genome, sequence, start, stop, orientation,
                 color='green'):
        self.name = name
        self.genome = genome
        self.sequence = sequence
        self.start = start
        self.stop = stop
        self.orientation = orientation
        self.color = color

    def __repr__(self):
        return "<Bookmark(%d, '%s', ...)>" % (self.id, self.name)

def create_a_bunch(session):
    session.add_all([
        Bookmark('a small bit', 'creature', 'chrI', 10, 500, +1),
        Bookmark('entire seq', 'creature', 'chrI', 0, 50000, +1),
        Bookmark('contig0 chunk', 'lamprey', 'Contig0', 0, 5000, +1),
        Bookmark('a contig49 chunk', 'lamprey', 'Contig49', 50000, 60000, +1),
        ])

def add_bookmark(name, genome, sequence, start, stop, orientation,
                 color, session=None):
    commit = False
    if session is None:
        commit = True
        session = db.get_session()
    b = Bookmark(name, genome, sequence, start, stop, orientation, color)
    session.add(b)

    if commit:
        session.commit()
    
def get_all(session, genome):
    q = session.query(Bookmark).filter(Bookmark.genome == genome).\
        order_by(Bookmark.name)

    return list(q)
