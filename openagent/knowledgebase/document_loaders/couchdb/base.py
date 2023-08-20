"""CouchDB client."""

from typing import Dict, List, Optional
from openagent.knowledgebase.document_loaders.basereader import BaseReader
from openagent.schema import DocumentNode
import logging
import json


class SimpleCouchDBReader(BaseReader):
    """Simple CouchDB reader.

    Concatenates each CouchDB doc into DocumentNode used by LlamaIndex.

    Args:
        couchdb_url (str): CouchDB Full URL.
        max_docs (int): Maximum number of documents to load.

    """

    def __init__(
        self,
        user: str,
        pwd: str,
        host: str,
        port: int,
        couchdb_url: Optional[Dict] = None,
        max_docs: int = 1000,
    ) -> None:
        """Initialize with parameters."""

        self.user = user

        import couchdb3

        if couchdb_url is not None:
            self.client: CouchDBClient = couchdb3.Server(couchdb_url)
        else:
            self.client: CouchDBClient = couchdb3.Server(
                f"http://{user}:{pwd}@{host}:{port}"
            )
        self.max_docs = max_docs

    def load_data(self, db_name: str, query: Optional[str] = None) -> List[DocumentNode]:
        """Load data from the input directory.

        Args:
            db_name (str): name of the database.
            query (Optional[str]): query to filter documents.
                Defaults to None

        Returns:
            List[DocumentNode]: A list of documents.

        """

        metadata = {
            "user": self.user,
            "db_name": db_name,
            "query": query
        }

        documents = []
        db = self.client.get(db_name)
        if query is None:
            # if no query is specified, return all docs in database
            logging.debug("showing all docs")
            results = db.view("_all_docs", include_docs=True)
        else:
            logging.debug("executing query")
            results = db.find(query)

        if type(results) is not dict:
            logging.debug(results.rows)
        else:
            logging.debug(results)

        # check if more than one result
        if type(results) is not dict and results.rows is not None:
            for row in results.rows:
                # check that the id field exists
                if "id" not in row:
                    raise ValueError("`id` field not found in CouchDB DocumentNode.")
                documents.append(DocumentNode(text=json.dumps(row.doc), extra_info=metadata))
        else:
            # only one result
            if results.get("docs") is not None:
                for item in results.get("docs"):
                    # check that the _id field exists
                    if "_id" not in item:
                        raise ValueError("`_id` field not found in CouchDB DocumentNode.")
                    documents.append(DocumentNode(text=json.dumps(item), extra_info=metadata))

        return documents
