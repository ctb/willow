from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_Session = None

def make_engine():
    global _engine, _Session

    if _engine is None:
        _engine = create_engine('sqlite:///:memory:', echo=True)
        _Session = sessionmaker()
        _Session.configure(bind=_engine)

    return _engine, _Session

def get_session():
    return _Session()

def create():
    from . import bookmarks

    engine, _ = make_engine()
    metadata = bookmarks.Bookmark.metadata

    metadata.create_all(engine)

    session = get_session()
    bookmarks.create_a_bunch(session)
    session.commit()
