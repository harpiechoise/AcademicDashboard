from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Postgres db connection
ENGINE = create_engine(
    f'postgresql://{os.getenv("DB_USER", "postgres")}:{os.getenv("DB_PASSWORD", "development123")}@{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", "5432")}/{os.getenv("DB_NAME", "raw_articles")}'
)

LocalSession = sessionmaker(bind=ENGINE)
