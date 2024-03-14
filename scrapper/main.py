from src.tools.search import PubMed, ScopusSearch, AbstractSearch
from src.database.models import Base
from src.database.connection import LocalSession
from threading import Thread
from src.logs.logger import logger
from sqlalchemy.orm import Session
import os
import sys


if len(sys.argv) > 1 and sys.argv[1] == "create":
    from src.database.connection import ENGINE

    Base.metadata.create_all(ENGINE)  # Creamos las tablas


def t_runner(
    min_year: str, max_year: str, session: Session, search_instance: AbstractSearch
) -> None:
    """Función que corre el hilo"""
    logger.info(f"Starting thread for {min_year} to {max_year}")
    for year in range(int(min_year), int(max_year)):
        logger.debug(f"Searching for {year}")
        search_instance(str(year))


def main():
    logger.debug("Starting main function...")
    min_year, max_year = os.getenv("MIN_YEAR", "2010"), os.getenv("MAX_YEAR", "2024")
    session_pubmed = LocalSession()
    session_scopus = LocalSession()

    pubmed = PubMed(session=session_pubmed)
    scopus = ScopusSearch(session=session_scopus)

    t_pubmed = Thread(
        target=t_runner, args=(min_year, max_year, session_pubmed, pubmed)
    )
    t_scopus = Thread(
        target=t_runner, args=(min_year, max_year, session_scopus, scopus)
    )

    t_pubmed.start()
    t_scopus.start()

    t_pubmed.join()
    t_scopus.join()
    logger.debug("Ending main function...")


if __name__ == "__main__":
    main()
