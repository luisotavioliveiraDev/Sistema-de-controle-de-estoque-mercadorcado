from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./estoque.db"
# Depois, no PostgreSQL:
# DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/estoque"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # só para SQLite; remova no PostgreSQL
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()