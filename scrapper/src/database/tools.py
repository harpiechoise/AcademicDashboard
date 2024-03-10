from src.database.models import Author, Article
from src.logs.logger import logger


def insert_data(session, data: dict) -> None:
    """Inserta los datos devueltos por los motores de busqueda en la base de datos

    Args:
        session (Session): Es una sesion de sqlalchemy para interactuar con la base de datos
        data (dict): Es un diccionario con los datos a insertar en la base de datos
    """
    # Make authors
    if not data:
        logger.error("[DATABASE] No data to insert discarding...")
        return
    if not data.get("authors"):
        logger.error("[DATABASE] No authors to insert discarding...")
        return
    authors = data.pop("authors")

    logger.debug("[DATABASE] Inserting data into database")
    # Make article
    # Try to get the article by title
    article_ = session.query(Article).filter_by(title=data["title"]).first()
    if article_:
        logger.info(f"[DATABASE] Article {article_} already exists")
        return
    else:
        logger.info("[DATABASE] Article does not exist, creating...")
        article = Article(
            doi=data["doi"],
            title=data["title"],
            publication_date=data["publication_date"],
            publisher=data["publisher"],
            reference_count=data["reference_count"],
            url=data["url"],
            issn=data["issn"],
        )
        session.add(article)

    for author in authors:
        # Try to get
        author_ = session.query(Author).filter_by(**author).first()
        if author_:
            logger.debug(f"[DATABASE] Author {author_} already exists")
            authors[authors.index(author)] = author_
        else:
            logger.debug("[DATABASE] Author does not exist, creating...")
            authors[authors.index(author)] = Author(**author)

    session.add_all(authors)
    session.commit()
    # relationship author_article
    for author in authors:
        article.authors.append(author)
    session.commit()
    logger.info("[DATABASE] Data inserted successfully")
