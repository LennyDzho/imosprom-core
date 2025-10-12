# Техническое задание: Gateway & UI-Backend

## Назначение

Единая точка входа для пользовательских клиентов (веб-виджет, кабинет, операторская панель). Обеспечивает HTTP/WS API, аутентификацию, валидацию и проксирование к шине сообщений (FastStream/RabbitMQ) и сервисам. Связан с **Agent Core** (RAG) и **Ticketing/Operators**. Работает с диалогами/задачами через `dialog_id` и `task_id`.

## Роли и аутентификация

* **Пользователь** (`role=user`): создаёт диалоги/сообщения, получает ответы.
* **Оператор** (`role=operator`): принимает эскалации, отвечает пользователям.
* **Админ** (`role=admin`) (опц.): доступ к настройкам/логам.
* Auth: JWT (Bearer) или session cookies; CORS; CSRF для web; RBAC по ролям.

## Интерфейсы (REST)

### Пользовательский чат

* `POST /api/v1/dialogs` → `{dialog_id}` — создать диалог.
* `POST /api/v1/dialogs/{dialog_id}/messages` → отправить сообщение пользователя.

  * Тело:

    ```json
    {
      "task_id": "optional-uuid",
      "text": "string",
      "lang": "ru",
      "kb_filters": {"product":"AppX","version":"1.2"},
      "model": "optional-model-name"
    }
    ```
  * Действия:

    1. Создаёт `task_id` (если не передан), валидирует.
    2. Публикует RPC запрос в RabbitMQ → `agent.handle.request` с `{dialog_id, task_id, trace_id, message, context, model}`.
    3. Возвращает `{dialog_id, task_id}`.

* `GET /api/v1/dialogs/{dialog_id}` → метаданные + последние сообщения (пагинация).
* `GET /api/v1/dialogs/{dialog_id}/tasks/{task_id}` → детали задачи, текущий статус, цитаты.

### Операторская панель

* `GET /api/v1/operators/me/assignments?state=assigned|accepted` — мои назначения.
* `POST /api/v1/operators/assignments/{assignment_id}/accept` — принять задачу.
* `POST /api/v1/operators/assignments/{assignment_id}/reply` — ответить пользователю.

  * Тело: `{ "text":"string" }` → сохраняет сообщение `role=operator`, публикует событие ответа.
* `POST /api/v1/operators/assignments/{assignment_id}/close` — закрыть задачу.

### Админ/Справочники (опц.)

* `GET /api/v1/models` — список доступных моделей (проксируется из Agent Core/конфига).
* `GET /api/v1/kb/search?q=...&product=...` — прямой поиск по KB (опционально; иначе через Agent Core).

## Интерфейсы (WebSocket/SSE)

* `GET /ws?dialog_id=...` — подписка пользователя на события диалога:

  * `message.created` (user/agent/operator)
  * `task.updated` (`status`, `action`, `confidence`)
  * `agent.reply.delta` (стриминг чанков)
  * `agent.reply.final`
  * `task.escalated` (покажем пользователю, что подключается оператор)
* `GET /ws/operators` — канал для операторов:

  * `operator.assignment.created` (новая заявка)
  * `dialog.updated`, `message.created`

## Взаимодействие с RabbitMQ (FastStream)

* **RPC → Agent Core**:

  * **Request** (routing key: `agent.handle.request`):

    ```json
    {
      "dialog_id":"uuid",
      "task_id":"uuid",
      "trace_id":"uuid",
      "model":"optional",
      "message": {"text":"...","lang":"ru"},
      "context": {"history":[{"role":"user","text":"..."}],"kb_filters":{}}
    }
    ```
  * **Response** (routing key: `agent.handle.response`):

    ```json
    {
      "dialog_id":"uuid",
      "task_id":"uuid",
      "trace_id":"uuid",
      "model":"resolved-model",
      "action":"auto|clarify|escalate",
      "confidence":0.82,
      "reply": {"text":"...","citations":[{"id":"KB-123","title":"...","url":"..."}]},
      "escalation": {
        "summary":"...",
        "recommended_queue":"billing_level1",
        "suggested_macros":["..."]
      }
    }
    ```
* **События для UI** (fan-out из Gateway):

  * `message.created` / `agent.reply.delta|final` / `task.updated` / `task.escalated`.

## Потоки

1. **Пользователь → Agent Core**

   * REST `POST /dialogs/{id}/messages` → публикация RPC → ожидание ответа → пуш в WS `agent.reply.delta|final` → сохранение сообщения в хранилище (через Ticketing) + обновление `task.status/action/confidence`.

2. **Эскалация → Оператор**

   * Если `action=escalate`, Gateway вызывает Ticketing/Operators:

     1. создаёт карточку эскалации,
     2. подбирает наименее загруженного оператора (по API Operators),
     3. создаёт назначение и пушит `operator.assignment.created` в `/ws/operators`.
   * Ответ оператора через `POST /operators/assignments/{id}/reply` → сообщение пользователю по WS.

## Ошибки и коды

* `400` — неверный payload, отсутствует `dialog_id`.
* `401/403` — нет аутентификации/прав.
* `404` — диалог/задача не найдены/не ваши.
* `409` — конфликт состояния (закрытый диалог, повторная отправка).
* `502` — таймаут RPC к Agent Core.
* `503` — перегрузка/пауза обслуживания.

Тело ошибки (JSON): `{ "error":"VALIDATION_ERROR", "message":"...", "trace_id":"..." }` (см. `src/core/infra`).

## Совместимость с Agent Core

* Форматы запрос/ответ строго соответствуют контракту Agent Core (см. спецификацию). При отсутствии `model` — проксируется `null`, выбор модели делает Agent Core (OpenRouter → Gemini fallback).

