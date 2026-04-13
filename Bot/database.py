import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def _default_sqlite_url():
    data_dir = Path(
        os.getenv("DATA_DIR", Path(__file__).resolve().parent / "database")
    ).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'clients.sqlite').as_posix()}"


SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _default_sqlite_url())

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
