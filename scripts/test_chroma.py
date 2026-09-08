from freelance_assistant.infrastructure.vector_store.chroma_client import ChromaClient

def test_chroma():
    client = ChromaClient()
    # Попробуем добавить тестовый вектор
    client.collection.add(
        ids=["test_id"],
        embeddings=[[0.1, 0.2, 0.3] * 512],  # длина должна соответствовать размерности модели
        metadatas=[{"test": "data"}]
    )
    print("ChromaDB работает, коллекция создана или уже существует.")

if __name__ == "__main__":
    test_chroma()