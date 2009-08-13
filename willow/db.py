from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_Session = None

def make_engine(uri):
    global _engine, _Session

    if _engine is None:
        _engine = create_engine(uri, echo=True)
        _Session = sessionmaker()
        _Session.configure(bind=_engine)

    return _engine, _Session

def get_session():
    return _Session()

def create(uri='sqlite:///:memory:'):
    from . import bookmarks

    engine, _ = make_engine(uri)
    metadata = bookmarks.Bookmark.metadata

    metadata.create_all(engine)

    ## @CTB
    from bookmarks import Bookmark
    session = get_session()
    q = session.query(Bookmark).first()
    if not q:
        bookmarks.create_a_bunch(session)
        session.commit()
