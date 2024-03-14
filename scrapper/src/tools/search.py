"""Es un motor de ingestión de articulos cientificos para su posterior analisis."""

from abc import ABC
from time import sleep
import os
import requests as req
from src.logs.logger import logger
from src.database.tools import insert_data


def crossref_helper(parse_function: callable) -> dict:
    """Añade información de crossref a la metadata de un artículo obtenida de otra fuente como PubMed o Scopus a través de su DOI

    Args:
        parse_function (callable): Función que parsea la metadata de un artículo

    Returns:
        dict: Metadata del artículo con información de crossref
    """

    def cross_ref_appender(*args, **kwargs):
        result = parse_function(*args, **kwargs)
        if result is None:
            logger.debug("[crossref_helper] DOI not found in the result")
            return None
        logger.info("[crossref_helper] Crossref found")
        doi = result["doi"]
        url = f"https://api.crossref.org/works/{doi}"
        response = req.get(url)
        if response.status_code != 200:
            return dict(**result, issn=None, url=None, reference_count=None)
        else:
            logger.debug(
                "[crossref_helper] Response was not sucessful. Response status code: {}".format(
                    response.status_code
                )
            )
        response = response.json()
        issn = response["message"].get("ISSN", None)
        if isinstance(issn, list):
            issn = issn[0]
        url = response["message"].get("URL", None)
        authors = []
        if "author" not in response["message"]:
            logger.debug(
                "[crossref_helper] Authors not found in the response, discarding..."
            )
            return None
        for author in response["message"]["author"]:
            # Affiliations
            affiliations = []
            if "affiliation" in author:
                for affiliation in author["affiliation"]:
                    affiliations.append(affiliation["name"])

            authors.append(
                {
                    "ORCID": author.get("ORCID", None),
                    "family": author.get("family", None),
                    "given": author.get("given", None),
                    "sequence": author.get("sequence", None),
                    "affiliation": affiliations,
                }
            )
        funders = []
        if "funder" in response["message"]:
            for funder in response["message"]["funder"]:
                funders.append(
                    {
                        "name": funder.get("name", None),
                        "doi": funder.get("DOI", None),
                        "url": funder.get("url", None),
                        "award": funder.get("award", None),
                    },
                )

        reference_count = response["message"]["reference-count"]
        publisher = response["message"]["publisher"]
        if authors:
            result["authors"] = authors
        if funders:
            result["funders"] = funders

        return dict(
            **result,
            issn=issn,
            url=url,
            reference_count=reference_count,
            publisher=publisher,
        )

    return cross_ref_appender


# Definir una estructura que represente un motor de búsqueda
class AbstractSearch(ABC):
    """Clase abstracta que representa un motor de búsqueda

    Args:
        ABC (ABC): Clase abstracta de Python
    """

    def __init__(self) -> None:
        """Base para un motor de busqueda de articulos cientificos."""
        pass

    def search(self, year: str) -> list[str]:
        """Método que realiza la búsqueda de artículos"""
        pass

    def search_for_article_metadata(self, id_: str) -> dict:
        """Método que busca la metadata de un artículo"""
        pass

    def get_doi(self, publication: dict) -> str:
        """Método que busca el DOI de un artículo"""
        pass


# Definir una estructura que represente un motor de búsqueda
class PubMed(AbstractSearch):
    """Es un motor de busqueda de articulos cientificos que toma la información que se necesita para el analisis
    por pais y año.

    El termino de busqueda se obtiene desde las variables de entorno.

        Ejemplo de uso:
        ```python
            from db import myDBSession
            pubmed = PubMed(session=myDBSession())
            # Buscar articulos en PubMed que se publicaron en el año 2021
            pubmed('2021')
        ```

    Args:
        AbstractSearch (AbstractSearch): Define los métodos base que debe tener un motor de busqueda
    """

    def __init__(self, session) -> None:
        """Inicializa el motor de busqueda de PubMed

        Args:
            session (Session): Es la sesion de SQLAlchemy que se utiliza para interactuar con la base de datos.
        """
        AbstractSearch.__init__(self)
        self.session = session

    def search(self, year: str) -> list[str]:
        """Realiza la busqueda de articulos en PubMed, utilizando la API de eutils


        Args:
            year (str): Año de publicación de los articulos

        Returns:
            list[str]: Lista de identificadores de los articulos encontrados
        """
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "term": f"{os.getenv('TOPIC', 'Climate change')}+AND+{year}",
            "db": "pubmed",
            "retmode": "json",
            "retmax": 500,
            "useHistory": "y",
        }

        response = req.get(url, params=params)
        logger.debug("[PubMed] Request to PubMed API with url: {}".format(response.url))
        logger.debug("[PubMed] Response status code: {}".format(response.status_code))

        if not response.ok:
            logger.error(
                "[PubMed] Request failed with status code: {}".format(
                    response.status_code
                )
            )
            logger.info("[PubMed] Fatal error, returning empty list...")
            return []

        ids = response.json()["esearchresult"]["idlist"]
        return ids

    def search_for_article_metadata(self, id_: str) -> dict:
        """Busca la metadata de un articulo en PubMed, utilizando la API de eutils
        Y el identificador del articulo para buscar la metadata y retornamos toda la metadata del articulo.

        Args:
            id_ (str): Identificador del articulo en PubMed.

        Returns:
            dict: Metadata del articulo en formato JSON.
        """

        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": id_,
            "retmode": "json",
        }

        response = req.get(url, params=params)
        if response.status_code != 200:
            logger.error(
                "[PubMed] Request failed with status code: {}".format(
                    response.status_code
                )
            )
            logger.info("[PubMed] Fatal error, returning None...")
            return None
        return response.json()["result"]

    def get_doi(self, publication: dict) -> str:
        """Obtiene el DOI de un articulo en PubMed, utilizando la metadata del articulo.

        Args:
            publication (dict): Metadata del articulo.

        Returns:
            str: DOI del articulo.
        """
        pubid = publication["uids"][0]
        article_info = publication[pubid]
        article_id = article_info["articleids"]
        for id_ in article_id:
            if id_["idtype"] == "doi":
                logger.info("[PubMed] DOI found")
                return id_["value"]
        logger.info("[PubMed] DOI not found")
        return None

    @crossref_helper
    def parse_result(self, publication: dict) -> dict:
        """Parsea la metadata de un articulo en PubMed, para obtener la información necesaria para el analisis.
        además de eso usa información de crossref para completar la metadata.

        Args:
            publication (dict): Metadata del articulo.

        Returns:
            dict: Información necesaria para el analisis.
        """
        uid = publication["uids"][0]
        article_info = publication[uid]
        lang = article_info["lang"]
        doi = self.get_doi(publication)

        source = article_info["source"]
        publication_date = article_info["pubdate"]
        title = article_info["title"]

        authors = []
        for author in article_info["authors"]:
            authors.append(author["name"])
        logger.info("[PubMed] Article parsed")
        return {
            "author": authors,
            "title": title,
            "publication_date": publication_date,
            "doi": doi,
            "source": source,
            "uid": uid,
            "language": lang,
        }

    def __call__(self, year: str) -> list[str]:
        """Método que realiza la busqueda de articulos en PubMed, utilizando la API de eutils
        por año y lo inserta en la base de datos."""
        logger.info(
            "[PubMed] Searching for articles in topic {} and year {}".format(
                os.getenv("TOPIC", "Climate change"), year
            )
        )
        ids = self.search(year)
        for id_ in ids:
            art = self.search_for_article_metadata(id_)
            insert_data(self.session, self.parse_result(art))
            logger.info(
                "[PubMed] Article: {}. Inserted to database".format(
                    art[art["uids"][0]]["title"]
                )
            )
            sleep(15)

    def __del__(self) -> None:
        """Cierra la sesion de SQLAlchemy"""
        self.session.close()
        logger.info("[Scopus] Session closed")


class ScopusSearch(AbstractSearch):
    """Es un motor de busqueda de articulos cientificos que toma la información que se necesita para el analisis
    por pais y año.

    El termino de busqueda se obtiene desde las variables de entorno.

    Ejemplo de uso:
    ```python
        from db import myDBSession
        scopus = ScopusSearch(session=myDBSession())
        # Buscar articulos en Scopus que se publicaron en el año 2021
        scopus('2021')
    ```

    Args:
        AbstractSearch (AbstractSearch): Define los métodos base que debe tener un motor de busqueda
    """

    def __init__(self, session) -> None:
        """Inicializa el motor de busqueda de Scopus


        Args:
            session (_type_): _description_
        """
        AbstractSearch.__init__(self)
        self.session = session

    def search(self, year: str, start=0) -> list[str]:
        """Realiza la busqueda de articulos en Scopus, utilizando la API de Elsevier
           El Api key se obtiene desde las variables de entorno.
        Args:
            year (str): Año de publicación de los articulos
            start (int): Paginación de la busqueda.
        Returns:
            list[str]: Lista de identificadores de los articulos encontrados
        """
        # Using scopus search API
        url = "https://api.elsevier.com/content/search/scopus"
        headers = {
            "Accept": "application/json",
            "X-ELS-APIKey": os.getenv(
                "SCOPUS_API_KEY", "a26927a66390986f8caecd36ea1843a2"
            ),
        }

        params = {
            "apiKey": os.getenv("SCOPUS_API_KEY", "a26927a66390986f8caecd36ea1843a2"),
            "query": os.getenv("TOPIC", "Climate change"),
            "date": f"{year}",
            "sort": "relevancy",
            "count": 10,
            "start": start,
        }

        response = req.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()["search-results"]["entry"]
        else:
            logger.error(
                "[Scopus] Request failed with status code: {}".format(
                    response.status_code
                )
            )
            logger.info("[Scopus] Fatal error, returning empty list...")
            return []

    def search_for_article_metadata(self, id_: str) -> dict:
        """Busca la metadata de un articulo en Scopus, utilizando la API de Elsevier,
        La api de elsevier nos da la metadata del articulo, por lo tanto, no es necesario buscar la metadata.
        """
        # Scopus gives the metadata of the article
        pass

    def get_doi(self, publication: dict) -> str:
        """Obtiene el DOI de un articulo en Scopus, utilizando la metadata del articulo."""
        doi = publication.get("prism:doi", None)
        if doi:
            logger.info("[Scopus] DOI found")
            return doi
        logger.info("[Scopus] DOI not found")
        return None

    @crossref_helper
    def parse_result(self, publication: dict) -> dict:
        """Parsea la metadata de un articulo en Scopus, para obtener la información necesaria para el analisis.
        además de eso usa información de crossref para completar la metadata.

        Args:
            publication (dict): Metadata del articulo.

        Returns:
            dict: Información necesaria para el analisis.
        """
        doi = self.get_doi(publication)
        if doi is None:
            return None
        title = publication["dc:title"]
        publication_date = publication["prism:coverDate"]
        authors = []
        authors.append(publication["dc:creator"])
        logger.info("[Scopus] Article parsed")
        return {
            "author": authors,
            "title": title,
            "publication_date": publication_date,
            "doi": doi,
        }

    def __call__(self, year: str) -> list[str]:
        """Método que realiza la busqueda de articulos en Scopus, utilizando la API de Elsevier
        por año y lo inserta en la base de datos."""
        logger.info(
            "[Scopus] Searching for articles in topic {} and year {}".format(
                os.getenv("TOPIC", "Climate change"), year
            )
        )
        for i in range(0, 500, 10):
            logger.info("[Scopus] Requesting articles from {} to {}".format(i, i + 10))
            for publication in self.search(year, start=i):
                insert_data(self.session, self.parse_result(publication))
                logger.info(
                    "[Scopus] Article: {}. Inserted to database".format(
                        publication["dc:title"]
                    )
                )

                sleep(10)

    def __del__(self) -> None:
        """Cierra la sesion de SQLAlchemy"""
        self.session.close()
        logger.info("[Scopus] Session closed")
