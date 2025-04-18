import time
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple

from pymilvus import Collection, connections, utility
from pymilvus import CollectionSchema, FieldSchema, DataType

from shared.logging import logger
from .models import (
    MilvusConfig,
    MilvusCollection,
    MilvusDocument,
    MilvusSearchResult,
    MilvusQueryResponse,
)


class MilvusDriver:
    """Driver for interacting with Milvus vector database"""

    def __init__(self, config: MilvusConfig):
        """Initialize the Milvus driver with given configuration

        Args:
            config: Configuration for Milvus connection
        """
        self.config = config
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Milvus server"""
        try:
            connections.connect(
                alias="default",
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                secure=self.config.secure,
            )
            logger.info(f"Connected to Milvus at {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close connection to Milvus server"""
        try:
            connections.disconnect("default")
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {str(e)}")

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        return utility.has_collection(collection_name)

    def create_collection(self, collection_config: MilvusCollection) -> None:
        """Create a new collection in Milvus

        Args:
            collection_config: Configuration for the collection
        """
        if self.collection_exists(collection_config.collection_name):
            logger.warning(
                f"Collection {collection_config.collection_name} already exists"
            )
            return

        # Define fields for the collection
        fields = [
            FieldSchema(
                name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=collection_config.dimension,
            ),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]

        # Create schema and collection
        schema = CollectionSchema(fields)
        collection = Collection(
            name=collection_config.collection_name, schema=schema, using="default"
        )

        # Create index
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": collection_config.index_type,
                "metric_type": collection_config.metric_type,
                "params": collection_config.index_params,
            },
        )

        logger.info(
            f"Created collection {collection_config.collection_name} with dimension {collection_config.dimension}"
        )

    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection

        Args:
            collection_name: Name of the collection to drop
        """
        if not self.collection_exists(collection_name):
            logger.warning(f"Collection {collection_name} does not exist")
            return

        utility.drop_collection(collection_name)
        logger.info(f"Dropped collection {collection_name}")

    def insert_documents(
        self, collection_name: str, documents: List[MilvusDocument]
    ) -> List[str]:
        """Insert documents into a collection

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert

        Returns:
            List of document IDs
        """
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = Collection(collection_name)

        # Prepare data
        ids = []
        vectors = []
        metadata_list = []

        for doc in documents:
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            vectors.append(doc.vector)
            metadata_list.append(doc.metadata)

        # Insert data
        collection.insert([ids, vectors, metadata_list])
        collection.flush()

        logger.info(f"Inserted {len(documents)} documents into {collection_name}")
        return ids

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
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = Collection(collection_name)
        collection.load()

        # Get default search params if not provided
        if search_params is None:
            search_params = {"nprobe": 16}

        # Start timing
        start_time = time.time()

        # Execute search
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["metadata"],
        )

        # Calculate time taken
        took_ms = (time.time() - start_time) * 1000

        # Format results
        search_results = []
        for hit in results[0]:
            search_results.append(
                MilvusSearchResult(
                    id=hit.id, score=hit.score, metadata=hit.entity.get("metadata", {})
                )
            )

        return MilvusQueryResponse(results=search_results, took_ms=took_ms)

    def delete_by_ids(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents by IDs

        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
        """
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = Collection(collection_name)
        collection.delete(expr=f"id in {ids}")

        logger.info(f"Deleted {len(ids)} documents from {collection_name}")

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary containing collection statistics
        """
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = Collection(collection_name)
        stats = collection.get_stats()

        return stats
