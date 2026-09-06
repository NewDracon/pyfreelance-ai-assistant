import chromadb
from chromadb.config import Settings as ChromaSettings
from freelance_assistant.core.config import settings
from typing import List, Dict, Any

class ChromaClient:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="orders",
            metadata={"hnsw:space": "cosine"}
        )

    def add_embedding(self, doc_id: str, embedding: List[float], metadata: Dict[str, Any]):
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def query(self, embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["metadatas", "distances"]
        )