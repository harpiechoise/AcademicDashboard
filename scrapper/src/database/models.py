from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from typing import Optional

Base = declarative_base()
# Make a relationship that an author can have many articles
# and an article can have many authors

# Association table
author_article = Table(
    "article_authors_relationship",
    Base.metadata,
    Column("author_id", Integer, ForeignKey("article_authors.id")),
    Column("article_id", Integer, ForeignKey("articles.id")),
)

author_affiliation = Table(
    "author_affiliation_relationship",
    Base.metadata,
    Column("author_id", Integer, ForeignKey("article_authors.id")),
    Column("affiliation_id", Integer, ForeignKey("affiliations.id")),
)


class Funder(Base):
    __tablename__ = "article_funders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name: Optional[str] = Column(String(200))
    doi: Optional[str] = Column(String(200))
    url: Optional[str] = Column(String(200))
    award: Optional[str] = Column(String(200))

    def __repr__(self):
        return f"<Funder(name={self.name})>"

    def __str__(self):
        return f"Funder ({self.name})"


article_funder = Table(
    "article_funder_relationship",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id")),
    Column("funder_id", Integer, ForeignKey("article_funders.id")),
)


class Affiliation(Base):
    __tablename__ = "affiliations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name: Optional[str] = Column(String(200))


class Author(Base):
    __tablename__ = "article_authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    family: Optional[str] = Column(String(45))
    given: Optional[str] = Column(String(45))
    sequence: Optional[str] = Column(String(45))
    ORCID: Optional[str] = Column(String(200))
    affiliation = relationship(
        Affiliation, secondary=author_affiliation, backref="affiliations", uselist=True
    )

    def __repr__(self):
        return f"<Author(name={self.family}, {self.given})>"

    def __str__(self):
        return f"Author ({self.family}, {self.given})"


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doi: Optional[str] = Column(String(500))
    title: Optional[str] = Column(String(500))
    publication_date: Optional[str] = Column(String(20))
    publisher: Optional[str] = Column(String(200))
    reference_count: Optional[int] = Column(Integer)
    url: Optional[str] = Column(String(500))
    issn: Optional[str] = Column(String(20))

    authors = relationship(
        Author, secondary=author_article, backref="authors", uselist=True
    )

    funders = relationship(
        Funder, secondary=article_funder, backref="funders", uselist=True
    )

    def __repr__(self):
        return f"<Article(title={self.title}, doi={self.doi})>"

    def __str__(self):
        return f"Article ({self.title}, {self.doi})"
