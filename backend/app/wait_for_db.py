import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings


def wait_for_db(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    engine = create_engine(settings.database_url)
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


if __name__ == "__main__":
    wait_for_db()
