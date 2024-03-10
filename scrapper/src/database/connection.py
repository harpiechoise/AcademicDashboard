from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os 
# Postgres db connection
ENGINE = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

LocalSession = sessionmaker(bind=ENGINE)