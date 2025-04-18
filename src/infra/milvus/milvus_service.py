from typing import Dict, List, Any, Optional, Union
import time
from functools import lru_cache

from shared.base import BaseService
from shared.logging import logger
from .milvus_driver import MilvusDriver
from .models import (
    MilvusConfig,
    MilvusCollection,
    MilvusDocument,
    MilvusSearchResult,
    MilvusQueryResponse,
)


class MilvusService(BaseService):
    """Service for interacting with Milvus vector database"""

    def __init__(self, config: MilvusConfig):
        """Initialize the Milvus service with given configuration

        Args:
            config: Configuration for Milvus connection
        """
        super().__init__()
        self.config = config
        self.driver = MilvusDriver(config=config)

    def process(self, inputs: Any) -> Any:
        """Process inputs based on operation type

        This is a generic method required by BaseService. For specific operations,
        use the dedicated methods below instead.

        Args:
            inputs: Dictionary containing operation and parameters

        Returns:
            Result of the operation
        """
        operation = inputs.get("operation")

        if operation == "search":
            return self.search(
                collection_name=inputs.get("collection_name"),
                query_vector=inputs.get("query_vector"),
                top_k=inputs.get("top_k", 10),
            )
        elif operation == "insert":
            return self.insert_documents(
                collection_name=inputs.get("collection_name"),
                documents=inputs.get("documents"),
            )
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    def create_collection(self, collection_config: MilvusCollection) -> None:
        """Create a new collection in Milvus

        Args:
            collection_config: Configuration for the collection
        """
        try:
            self.driver.create_collection(collection_config)
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise

    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection

        Args:
            collection_name: Name of the collection to drop
        """
        try:
            self.driver.drop_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to drop collection: {str(e)}")
            raise

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        return self.driver.collection_exists(collection_name)

    def insert_documents(
        self, collection_name: str, documents: List[MilvusDocument]
    ) -> List[str]:
        """Insert documents into a collection

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert

        Returns:
            List of inserted document IDs
        """
        try:
            return self.driver.insert_documents(collection_name, documents)
        except Exception as e:
            logger.error(f"Failed to insert documents: {str(e)}")
            raise

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
    ) -> MilvusQueryResponse:
        """Search for similar vectors in the collection

        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector
            top_k: Number of results to return
            search_params: Search parameters

        Returns:
            MilvusQueryResponse containing search results
        """
        try:
            return self.driver.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
                search_params=search_params,
            )
        except Exception as e:
            logger.error(f"Failed to search: {str(e)}")
            raise

    def delete_by_ids(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents by IDs

        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
        """
        try:
            self.driver.delete_by_ids(collection_name, ids)
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary containing collection statistics
        """
        try:
            return self.driver.get_collection_stats(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise

    def upsert_documents(
        self, collection_name: str, documents: List[MilvusDocument]
    ) -> List[str]:
        """Upsert documents (insert or update) into a collection

        Args:
            collection_name: Name of the collection
            documents: List of documents to upsert

        Returns:
            List of document IDs
        """
        # First delete any documents with matching IDs
        existing_ids = [doc.id for doc in documents if doc.id is not None]
        if existing_ids:
            self.delete_by_ids(collection_name, existing_ids)

        # Then insert all documents
        return self.insert_documents(collection_name, documents)

    def batch_search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
    ) -> List[MilvusQueryResponse]:
        """Perform batch search for multiple query vectors

        Args:
            collection_name: Name of the collection to search
            query_vectors: List of query vectors
            top_k: Number of results to return for each query
            search_params: Search parameters

        Returns:
            List of MilvusQueryResponse, one for each query vector
        """
        results = []
        for vector in query_vectors:
            result = self.search(
                collection_name=collection_name,
                query_vector=vector,
                top_k=top_k,
                search_params=search_params,
            )
            results.append(result)

        return results


@lru_cache(maxsize=1)
def get_milvus_service(host: str = "localhost", port: int = 19530) -> MilvusService:
    """Get a singleton instance of MilvusService

    Args:
        host: Milvus host
        port: Milvus port

    Returns:
        MilvusService instance
    """
    config = MilvusConfig(host=host, port=port)
    return MilvusService(config=config)
