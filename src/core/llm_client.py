import httpx
import json
from typing import Dict, Any, List
from src.core.config.settings import settings
from src.core.logging import logger


class OpenRouterClient:
    """
    Клиент для работы с OpenRouter API
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        self.fallback_model = settings.FALLBACK_MODEL
        self.timeout = 30.0

    async def generate_response(
            self,
            messages: List[Dict[str, str]],
            model: str = None,
            temperature: float = 0.7,
            max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Генерация ответа через OpenRouter
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Agent Core"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Sending request to OpenRouter with model: {model}")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully received response from OpenRouter")
                    return data
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")

                    # Попробуем fallback модель
                    if model != self.fallback_model:
                        logger.info(f"Trying fallback model: {self.fallback_model}")
                        return await self.generate_response(
                            messages,
                            self.fallback_model,
                            temperature,
                            max_tokens
                        )
                    else:
                        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

            except httpx.TimeoutException:
                logger.error("OpenRouter API timeout")
                raise Exception("OpenRouter API timeout")
            except Exception as e:
                logger.error(f"OpenRouter API exception: {e}")
                raise

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных моделей
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/models")
                if response.status_code == 200:
                    return response.json().get("data", [])
                else:
                    logger.error(f"Failed to fetch models: {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching models: {e}")
                return []


# Создаем глобальный экземпляр клиента
llm_client = OpenRouterClient()