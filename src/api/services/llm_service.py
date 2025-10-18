from typing import List, Dict, Any
from src.core.llm_client import llm_client
from src.core.logging import logger


class LLMService:
    """
    Сервис для работы с языковыми моделями через OpenRouter
    """

    def __init__(self):
        self.client = llm_client

    async def generate_rag_response(
            self,
            user_question: str,
            context_chunks: List[Dict[str, Any]],
            conversation_history: List[Dict[str, str]] = None,
            model: str = None
    ) -> Dict[str, Any]:
        """
        Генерация ответа с использованием RAG
        """

        context_text = self._build_context_from_chunks(context_chunks)
        system_prompt = self._get_system_prompt()

        messages = self._build_messages(
            system_prompt=system_prompt,
            context=context_text,
            user_question=user_question,
            history=conversation_history
        )

        try:
            response = await self.client.generate_response(
                messages=messages,
                model=model,
                temperature=0.1,
                max_tokens=1500
            )

            model_response = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            model_used = response["model"]

            logger.info(f"Generated response using model: {model_used}, tokens: {usage}")

            return {
                "response": model_response,
                "model": model_used,
                "usage": usage,
                "citations": self._extract_citations(context_chunks),
                "confidence": self._calculate_confidence(model_response, context_chunks)
            }

        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            raise

    def _build_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            source = chunk.get('source', 'Unknown')
            context_parts.append(f"[Источник {i}: {source}]\n{text}\n")
        return "\n".join(context_parts)

    def _get_system_prompt(self) -> str:
        return """Ты - AI ассистент службы поддержки. Используй предоставленный контекст для ответов.

ИНСТРУКЦИИ:
1. Отвечай ТОЛЬКО на основе предоставленного контекста
2. Если информации недостаточно, вежливо сообщи об этом
3. Будь точным и полезным
4. Цитируй источники, когда это уместно

Формат ответа:
- Четкий, структурированный ответ
- Указывай номера источников
- Будь дружелюбным и профессиональным"""

    def _build_messages(
            self,
            system_prompt: str,
            context: str,
            user_question: str,
            history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        user_message = f"""КОНТЕКСТ ДЛЯ ОТВЕТА:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_question}

Пожалуйста, ответь на вопрос пользователя, используя только предоставленный контекст."""

        messages.append({"role": "user", "content": user_message})
        return messages

    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for chunk in chunks:
            citations.append({
                "id": chunk.get('id'),
                "title": chunk.get('title', 'Unknown'),
                "url": chunk.get('url', ''),
                "score": chunk.get('score', 0.0)
            })
        return citations

    def _calculate_confidence(self, response: str, chunks: List[Dict[str, Any]]) -> float:
        if not chunks:
            return 0.1

        base_confidence = min(len(chunks) * 0.2, 0.8)

        response_lower = response.lower()
        uncertainty_indicators = [
            "не знаю", "не уверен", "нет информации",
            "не могу ответить", "извините"
        ]

        for indicator in uncertainty_indicators:
            if indicator in response_lower:
                base_confidence *= 0.5
                break

        return round(base_confidence, 2)


llm_service = LLMService()