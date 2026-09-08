import asyncio
from openai import AsyncOpenAI
from freelance_assistant.core.config import settings


async def test_openai():
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )

    # Тест эмбеддингов
    try:
        emb_response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input="Hello world"
        )
        print("Embedding успешно получен, длина:", len(emb_response.data[0].embedding))
    except Exception as e:
        print("Ошибка при получении эмбеддинга:", e)

    # Тест LLM (простейший запрос)
    try:
        chat_response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": "Привет! Ответь одним словом."}],
            temperature=0.3
        )
        print("LLM ответил:", chat_response.choices[0].message.content)
    except Exception as e:
        print("Ошибка при вызове LLM:", e)


if __name__ == "__main__":
    asyncio.run(test_openai())