import sqlite3
from typing import Generator
from contextlib import contextmanager

from config import DB_PATH
from .models import create_tables


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
  """
  Context manager that returns a SQLite connection.
  Ensures tables exist before use.
  """
  conn = sqlite3.connect(DB_PATH)
  try:
    # Make sure tables are created
    create_tables(conn)
    yield conn
  finally:
    conn.close()
