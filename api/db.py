from sqlmodel import create_engine, Session
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
password = quote_plus(os.getenv("DB_PASSWORD", ""))
DATABASE_URL = f"postgresql+psycopg2://{os.getenv("DB_USER")}:{password}@localhost/{os.getenv("DB_NAME")}"

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
