import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


async def test_openrouter_direct():
    """Прямой тест OpenRouter без зависимостей от settings"""
    print("🧪 Прямой тест OpenRouter...")

    # Читаем API ключ напрямую из .env
    api_key = None
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('OPENROUTER_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    # Убираем кавычки если есть
                    api_key = api_key.strip('"\'')
                    break
    except Exception as e:
        print(f"❌ Ошибка чтения .env: {e}")
        return

    if not api_key or api_key in ['sk-or-your-key-here', '']:
        print("❌ OPENROUTER_API_KEY не найден или имеет значение по умолчанию")
        print("💡 Проверьте что в .env файле есть строка: OPENROUTER_API_KEY=sk-or-v1-your-actual-key")
        return

    print(f"✅ API ключ найден: {api_key[:10]}...")

    # Прямой HTTP запрос к OpenRouter
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/agent-core",
        "X-Title": "Agent Core Test"
    }

    payload = {
        "model": "google/gemini-2.5-pro",
        "messages": [
            {"role": "user", "content": "Привет! Ответь одним предложением. Что такое искусственный интеллект?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    print("1. Отправляем тестовый запрос к OpenRouter...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                answer = data['choices'][0]['message']['content']
                model = data['model']
                print(f"✅ Запрос успешен!")
                print(f"🤖 Модель: {model}")
                print(f"💬 Ответ: {answer}")

                # Тестируем получение списка моделей
                print("2. Получаем список доступных моделей...")
                models_response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers
                )

                if models_response.status_code == 200:
                    models_data = models_response.json()
                    models_count = len(models_data.get('data', []))
                    print(f"✅ Доступно моделей: {models_count}")

                    # Покажем несколько моделей
                    free_models = [
                        m for m in models_data.get('data', [])
                        if m.get('pricing', {}).get('prompt') == '0'
                    ]

                    print(f"🆓 Бесплатные модели: {len(free_models)}")
                    for model in free_models[:3]:
                        print(f"   - {model['id']}")

                else:
                    print(f"⚠️  Не удалось получить список моделей: {models_response.status_code}")

            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"📄 Ответ: {response.text}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_openrouter_direct())