# Техническое задание: Frontend для Gateway & UI‑Backend

## 1. Цели и охват

**Цель:** предоставить единый фронтенд (веб‑виджет, пользовательский кабинет, операторская панель, админ‑экран) с real‑time взаимодействием (WS/SSE), соответствующий контрактам Gateway/API и сценариям Agent Core и Ticketing/Operators.

**Охват:**

* Аутентификация (JWT и Cookie‑сессии с CSRF).
* Пользовательский чат (диалоги, сообщения, стриминг, цитаты/источники).
* Эскалации к операторам (просмотр статуса, реальный диалог с оператором).
* Операторская панель (назначения, принятие, ответы, закрытие).
* Админ (список моделей, поиск по БЗ).
* Общее: уведомления, i18n, доступность (a11y), трекинг ошибок/метрик, работа с сетью (повтор, оффлайн‑очередь), защита от XSS/CSRF, RBAC.

## 2. Целевая аудитория и роли

* **Пользователь** (`role=user`): создаёт диалоги/сообщения, видит ответы, историю, цитаты.
* **Оператор** (`role=operator`): видит назначения, принимает/отвечает/закрывает.
* **Админ** (`role=admin`): получает справочную информацию (модели, KB поиск).

## 3. Платформы и требования к окружению

* **Браузеры:** последние 2 версии Chrome/Edge/Firefox/Safari, мобильные Safari/Chrome.
* **Адаптивность:** мобильный ≥360px, планшет, десктоп ≥1280px.
* **PWA (опц.):** иконки, offline‑splash, кеширование базовых статики (пригодно для виджета).

## 4. Технологии

* **Ядро:** React 18+, TypeScript 5+.
* **UI‑библиотека:** Chakra UI (темизация, светлая/тёмная темы), иконки lucide‑react.
* **Состояние:** React Query (серверное), Zustand (локальные стора/фичи), URL‑router (React Router 6+).
* **Формы:** React Hook Form + Zod.
* **Реал‑тайм:** WebSocket (приоритет) + SSE fallback (опц.).
* **Сборка:** Vite + ESLint/Prettier + Husky (pre‑commit).
* **Тесты:** Vitest (unit), Testing Library (components), Playwright (e2e).
* **i18n:** i18next (ru/en), ICU‑messages.
* **Аналитика/логи:** Sentry (errors, perf), PostHog/umami (события/пути) — по фиче‑флагу.

## 5. Архитектура фронтенда

* **Фиче‑модульная структура (FSD‑подобно):**

  * `app/` — init (router, i18n, theme, error boundary, query client), layout.
  * `pages/` — маршруты (auth, dialogs, dialog, operators, admin).
  * `widgets/` — крупные комбинированные блоки (DialogList, Composer, StreamPanel, AssignmentBoard).
  * `features/` — целевые действия (sendMessage, acceptAssignment, operatorReply, logout, etc.).
  * `entities/` — типы/модели (User, Dialog, Task, Message, Assignment, Model).
  * `shared/` — ui‑кит, api‑client, ws‑client, hooks, utils, config, RBAC‑guards.
* **API‑клиент:** fetch‑обёртка с:

  * авто‑подстановкой `Authorization: Bearer` при JWT‑режиме;
  * cookie‑режимом + `X‑CSRF‑Token` для защищённых методов;
  * централизованной обработкой 401/403 (редирект на /login, показ баннера «сессия истекла»);
  * ретраями с экспоненциальной паузой для идемпотентных GET.
* **WS‑клиент:** единый менеджер подключений c автопереподключением (jitter), backoff, multiplex по каналам пользователя и оператора.

## 6. Навигация и маршруты

* `/login`, `/register`, `/logout`.
* `/` → редирект по роли:

  * `user` → `/dialogs`.
  * `operator` → `/operators/assignments`.
  * `admin` → `/admin`.
* `/dialogs` — список диалогов.
* `/dialogs/:dialog_id` — детальный экран диалога.
* `/operators/assignments` — назначения (таб/фильтры `assigned|accepted`).
* `/admin` — справочники: модели, KB‑поиск.

## 7. Экранные формы и сценарии

### 7.1. Аутентификация

* **Register/Login:** формы (email, password, display_name* у регистрации).
* **JWT‑режим:** хранение access в памяти (не в localStorage), refresh — httpOnly cookie (или в памяти при strict‑режиме). Ротация по 401 на /refresh.
* **Cookie‑режим:** `sid` httpOnly, CSRF: захват `csrf` из `/auth/me` → добавлять `X‑CSRF‑Token`.
* **Успех:** редирект на роль‑зависимый маршрут. Ошибки: подсветка полей, toasts.

### 7.2. Пользовательский чат

* **Список диалогов (`/dialogs`):**

  * Поиск/фильтры, пагинация, бесконечная прокрутка.
  * Карточки: заголовок (или участник), последний месседж, статус `task.action/status/confidence`.
* **Экран диалога (`/dialogs/:id`):**

  * **Хедер:** `dialog_id`, статус (badge), выбор модели (если доступно), фильтры KB.
  * **Лента сообщений:** bubble‑вид, аватар (user/agent/operator), время, копирование.
  * **Цитаты/источники:** collapsible блок под ответом агента (title/url; иконка «ссылка»).
  * **Стриминг:** при `agent.reply.delta` добавлять чанки текста в текущий «typing» блок; `agent.reply.final` — заморозить блок.
  * **Composer:** textarea с autosize, отправка `Ctrl+Enter`, кнопка «Отправить», индикатор «агент печатает…». Поля: `text`, `lang`, `kb_filters`, `model`.
  * **WS события:**

    * `message.created` (user/agent/operator) → пуш в ленту.
    * `task.updated` → бейдж/статус.
    * `task.escalated` → плашка «подключается оператор».

### 7.3. Операторская панель

* **Назначения (`/operators/assignments`):**

  * Таб‑фильтры: `assigned`, `accepted`.
  * Таблица/доска: карточка назначения (пользователь, краткое описание/summary, SLA таймер).
  * Действия:

    * **Accept** → POST `/operators/assignments/{id}/accept`.
    * **Reply** → панель диалога: лента сообщений + composer (role=operator).
    * **Close** → POST `/operators/assignments/{id}/close`.
  * **WS канал `/ws/operators`:** `operator.assignment.created`, `dialog.updated`, `message.created`.

### 7.4. Админ/Справочники

* **Модели:** GET `/models` → таблица: имя, провайдер, доступность; быстрый поиск.
* **KB поиск:** форма (q, product, version), список результатов (title, snippet, url), переход.

## 8. Компоненты (основные)

* `DialogList`, `DialogItem`, `DialogHeader`, `MessageBubble`, `CitationsList`.
* `Composer`, `TypingIndicator`, `ModelSelect`, `KbFilters`.
* `AssignmentBoard`, `AssignmentCard`, `OperatorChatPane`.
* `AuthForm`, `RegisterForm`, `UserMenu`, `RbacGuard`.
* `ErrorBoundary`, `EmptyState`, `LoadingSkeleton`, `ToastCenter`.

## 9. Типы данных (TS, упрощённо)

```ts
type UUID = string;
export type Role = 'user' | 'operator' | 'admin';
export interface User { id: UUID; email: string; display_name: string; role: Role; }
export interface DialogMeta { id: UUID; created_at: string; title?: string; }
export type MessageRole = 'user' | 'agent' | 'operator';
export interface Citation { id: string; title: string; url: string; }
export interface Message { id: UUID; dialog_id: UUID; role: MessageRole; text: string; ts: string; citations?: Citation[]; }
export type TaskAction = 'auto' | 'clarify' | 'escalate';
export interface TaskInfo { id: UUID; status: string; action?: TaskAction; confidence?: number; }
export interface Assignment { id: UUID; dialog_id: UUID; state: 'assigned'|'accepted'; summary?: string; }
```

## 10. Сетевые контракты (клиент)

Ниже приведены **полные описания клиентских запросов** (REST) и контрактов событий (WS/SSE), соответствующие бэкенд‑ТЗ. Все примеры — в формате JSON. Если не указано иное, `Content-Type: application/json`.

### 10.1 Заголовки и общие правила

* **JWT‑режим**: `Authorization: Bearer <access-jwt>`.
* **Cookie‑режим**: `sid` в HttpOnly‑cookie + `X-CSRF-Token: <csrf>` для `POST/PUT/PATCH/DELETE`.
* **Idempotency (рекомендовано)**: `Idempotency-Key: <uuid>` для действий отправки сообщений.
* **Trace**: фронт может добавлять `X-Trace-Id: <uuid>` (отражается в error.trace_id).
* **Пагинация**: `?limit=<int>&offset=<int>` (если не указано иначе).

---

### 10.2 Auth

#### POST `/api/v1/auth/register`

**Body**

```json
{ "email":"user@example.com", "password":"P@ssw0rd!", "display_name":"Mik" }
```

**Response (JWT)**

```json
{ "user_id":"uuid", "email":"user@example.com", "role":"user", "access":"<jwt>", "refresh":"<jwt>" }
```

**Response (Cookie)**

* `Set-Cookie: sid=<session_id>; HttpOnly; Secure; SameSite=Strict`
* Body

```json
{ "user_id":"uuid", "email":"user@example.com", "role":"user", "csrf":"<csrf-token>" }
```

**Errors**: 400 (validation), 409 (email exists).

#### POST `/api/v1/auth/login`

**Body**

```json
{ "email":"user@example.com", "password":"P@ssw0rd!" }
```

**Response**: как для `/register` (режим зависит от конфигурации).
**Errors**: 400, 401 (bad credentials), 423 (опц., заблокированная учётка).

#### POST `/api/v1/auth/logout`

* В JWT‑режиме фронт просто забывает токены; сервер может инвалидацировать refresh.
* В Cookie‑режиме сервер ставит: `Set-Cookie: sid=; Max-Age=0`.
  **Response**: `204 No Content`.

#### POST `/api/v1/auth/refresh`

**Body (вариант)**

```json
{ "refresh":"<jwt>" }
```

**Response**

```json
{ "access":"<new-access>", "refresh":"<rotated-refresh-optional>" }
```

**Errors**: 401 (invalid/expired), 409 (reuse detected), 429 (too frequent).

#### GET `/api/v1/auth/me`

**Response**

```json
{ "user_id":"uuid", "email":"user@example.com", "display_name":"Mik", "role":"user" }
```

**Errors**: 401/403.

---

### 10.3 Диалоги и сообщения (Пользователь)

#### POST `/api/v1/dialogs`

**Response**

```json
{ "dialog_id":"uuid", "created_at":"2025-10-12T12:34:56Z" }
```

**Errors**: 401/403.

#### POST `/api/v1/dialogs/{dialog_id}/messages`

**Headers**: `Idempotency-Key` (рекоменд.), JWT/Cookie+CSRF.
**Body**

```json
{
  "task_id":"optional-uuid",
  "text":"Привет!",
  "lang":"ru",
  "kb_filters": {"product":"AppX","version":"1.2"},
  "model":"gpt-4o-mini"
}
```

**Response**

```json
{ "dialog_id":"uuid", "task_id":"uuid" }
```

**Server-side flow**: публикация RPC `agent.handle.request`.
**Errors**: 400 (validation), 401/403, 404 (dialog not found/alien), 409 (closed), 502 (RPC timeout), 503.

#### GET `/api/v1/dialogs/{dialog_id}`

**Query**: `?limit=30&offset=0`
**Response**

```json
{
  "dialog": {"id":"uuid", "title":null, "created_at":"..."},
  "messages": [
    {"id":"m1","role":"user","text":"...","ts":"..."},
    {"id":"m2","role":"agent","text":"...","ts":"...",
     "citations":[{"id":"KB-123","title":"...","url":"..."}]}
  ],
  "task": {"id":"uuid","status":"in_progress","action":"auto","confidence":0.82}
}
```

**Errors**: 401/403, 404.

#### GET `/api/v1/dialogs/{dialog_id}/tasks/{task_id}`

**Response**

```json
{
  "task": {
    "id":"uuid", "status":"in_progress",
    "action":"auto|clarify|escalate", "confidence":0.82,
    "last_reply": {"text":"...","citations":[{"id":"KB-123","title":"...","url":"..."}]}
  }
}
```

**Errors**: 401/403, 404.

---

### 10.4 Операторская панель

#### GET `/api/v1/operators/me/assignments`

**Query**: `?state=assigned|accepted&limit=50&offset=0`
**Response**

```json
{
  "items": [
    {
      "id":"uuid", "dialog_id":"uuid", "state":"assigned",
      "summary":"Краткое описание","created_at":"...", "sla_due_at":"..."
    }
  ],
  "total": 1
}
```

#### POST `/api/v1/operators/assignments/{assignment_id}/accept`

**Response**

```json
{ "id":"uuid", "state":"accepted", "accepted_at":"..." }
```

**Errors**: 401/403, 404, 409 (already accepted/closed).

#### POST `/api/v1/operators/assignments/{assignment_id}/reply`

**Body**

```json
{ "text":"Здравствуйте! Чем могу помочь?" }
```

**Response**

```json
{ "ok": true, "message_id":"uuid" }
```

**Side‑effect**: событие `message.created` для пользователя.
**Errors**: 400, 401/403, 404, 409.

#### POST `/api/v1/operators/assignments/{assignment_id}/close`

**Response**

```json
{ "id":"uuid", "state":"closed", "closed_at":"..." }
```

**Errors**: 401/403, 404, 409.

---

### 10.5 Админ/Справочники

#### GET `/api/v1/models`

**Response**

```json
{
  "models": [
    {"name":"gpt-4o-mini","provider":"openrouter","status":"available"},
    {"name":"gemini-1.5-pro","provider":"google","status":"degraded"}
  ]
}
```

#### GET `/api/v1/kb/search`

**Query**: `?q=очистка%20кеша&product=AppX&version=1.2&limit=20&offset=0`
**Response**

```json
{
  "results": [
    {"id":"KB-123","title":"Как очистить кеш","snippet":"...","url":"https://..."}
  ],
  "total": 1
}
```

---

### 10.6 Формат ошибок (единый)

**HTTP Codes**: 400, 401, 403, 404, 409, 429, 500, 502, 503.
**Body**

```json
{ "error":"VALIDATION_ERROR", "message":"Поле text обязательно", "trace_id":"e38e4f4baf" }
```

---

### 10.7 WebSocket/SSE: события и форматы

#### Пользовательский канал `GET /ws?dialog_id=<uuid>`

**Возможные события**

* `message.created`

```json
{ "type":"message.created", "dialog_id":"uuid", "message": {"id":"m3","role":"agent","text":"...","ts":"...","citations":[{"id":"KB-1","title":"...","url":"..."}]}}
```

* `agent.reply.delta`

```json
{ "type":"agent.reply.delta", "dialog_id":"uuid", "task_id":"uuid", "delta":"текстовый_чанк" }
```

* `agent.reply.final`

```json
{ "type":"agent.reply.final", "dialog_id":"uuid", "task_id":"uuid", "reply": {"text":"полный ответ","citations":[{"id":"KB-1","title":"...","url":"..."}]}}
```

* `task.updated`

```json
{ "type":"task.updated", "dialog_id":"uuid", "task": {"id":"uuid","status":"in_progress","action":"auto","confidence":0.82} }
```

* `task.escalated`

```json
{ "type":"task.escalated", "dialog_id":"uuid", "task_id":"uuid", "summary":"..." }
```

#### Операторский канал `GET /ws/operators`

* `operator.assignment.created`

```json
{ "type":"operator.assignment.created", "assignment": {"id":"uuid","dialog_id":"uuid","state":"assigned","summary":"..."} }
```

* `dialog.updated`

```json
{ "type":"dialog.updated", "dialog": {"id":"uuid","last_message_preview":"...","updated_at":"..."} }
```

* `message.created` (зеркально пользовательскому)

**Протокол**: текстовый JSON‑кадр на событие. Пинги сервера или клиентские ping/pong (опц.) — через специальные кадры `{ "type":"ping" }`.

---

### 10.8 Клиентские интерфейсы (TypeScript)

```ts
// Auth
auth.register(data: {email: string; password: string; display_name: string}): Promise<{user_id: string; email: string; role: Role; access?: string; refresh?: string; csrf?: string}>;
auth.login(data: {email: string; password: string}): Promise<...>;
auth.logout(): Promise<void>;
auth.refresh(body?: {refresh: string}): Promise<{access: string; refresh?: string}>;
auth.me(): Promise<User>;

// Dialogs
dialogs.create(): Promise<{dialog_id: string; created_at: string}>;
dialogs.get(dialog_id: string, q?: {limit?: number; offset?: number}): Promise<{dialog: DialogMeta; messages: Message[]; task?: TaskInfo}>;
dialogs.send(dialog_id: string, body: {task_id?: string; text: string; lang?: string; kb_filters?: Record<string,string>; model?: string}, headers?: {idempotencyKey?: string}): Promise<{dialog_id: string; task_id: string}>;

'tasks.get'(dialog_id: string, task_id: string): Promise<{task: TaskInfo & {last_reply?: {text: string; citations?: Citation[]}}}>;

// Operators
operators.assignments.list(q?: {state?: 'assigned'|'accepted'; limit?: number; offset?: number}): Promise<{items: Assignment[]; total: number}>;
operators.assignments.accept(id: string): Promise<{id: string; state: 'accepted'; accepted_at: string}>;
operators.assignments.reply(id: string, data: {text: string}): Promise<{ok: true; message_id: string}>;
operators.assignments.close(id: string): Promise<{id: string; state: 'closed'; closed_at: string}>;

// Admin
admin.models.list(): Promise<{models: {name: string; provider: string; status: string}[]}>;
admin.kb.search(q: {q: string; product?: string; version?: string; limit?: number; offset?: number}): Promise<{results: {id: string; title: string; snippet: string; url: string}[]; total: number}>;
```

---

## 11. Производительность и UX‑детали

Производительность и UX‑детали

* **Бюджеты:** LCP ≤ 2.5s (3G Fast), TTI ≤ 3s, bundle ≤ 250KB (инициал), code‑split маршрутов.
* **Скелетоны/плейсхолдеры:** для списков, ленты, форм.
* **Пагинация:** бесконечный скролл с `React Query` (cursor‑based, если доступно), иначе page‑based.
* **Дефолтные тексты:** пустые состояния, ошибки сети, таймаут Agent Core.
* **Клавиатурные шорткаты:** `Ctrl+Enter` — отправка; `Esc` — отмена ввода; `/` — фокус поиска.

## 12. Безопасность

* XSS: экранирование, безопасный рендер ссылок/цитат (noopener, noreferrer).
* CSRF: обязательный `X‑CSRF‑Token` при cookie‑режиме.
* CORS: только доверенные origin (env‑переменная), `credentials` опционально.
* RBAC‑гварды на маршрутах и элементах UI.

## 13. Надёжность сети

* **WS переподключение:** backoff 1‑2‑4‑8‑… до 60s, jitter, детект `visibilitychange`.
* **Очередь оффлайн‑отправок:** локальная (IndexedDB/Memory) с повторной доставкой после `online`.
* **Таймауты:** REST 15s, WS ping/pong 25s, user‑feedback (баннер «соединение потеряно»).

## 14. Логи/метрики

* Ошибки JS/ресурсов → Sentry.
* Пользовательские события: отправка сообщения, эскалация, ответ оператора, закрытие — в Analytics (флаги).
* Перф: Web‑Vitals (LCP, CLS, FID), отчёт в консоль dev и отправка на сервер (опц.).

## 15. Локализация и доступность

* i18n: RU/EN, хранение языка в профиле/локали браузера.
* a11y: роли/aria‑атрибуты, контраст ≥ 4.5:1, фокус‑кольца, читабельные шрифты.

## 16. Темизация и дизайн‑система

* Chakra theme tokens: цвета, spacing, размеры.
* Компонентные варинты: `Button`, `Badge` (status: success/warn/error/info), `Card`, `Tabs`, `Table`, `Modal`.
* Светлая/тёмная темы (system‑prefers‑color‑scheme), сохранение выбора пользователя.

## 20. Краевые случаи и обработка ошибок

* Таймаут RPC → показать плашку `502 / агент временно недоступен`, кнопка «Повторить».
* Потеря WS → баннер «Соединение потеряно» + авто‑ретрай.
* 401/403 → редирект на /login (с сохранением `redirectTo`).
* 404 (диалог/задача) → EmptyState с кнопкой «Вернуться к списку».
* 409 (конфликт) → всплывающее уведомление и повторная загрузка задачи.

## 22. Приёмочные критерии (сжатые)

1. Пользователь может создать диалог, отправить сообщение и увидеть потоковый ответ агента с цитатами.
2. При `action=escalate` пользователь видит индикатор эскалации; оператор получает карточку, принимает, отвечает — пользователь видит ответ по WS.
3. Auth работает в двух режимах (JWT и Cookie+CSRF); `GET /auth/me` корректно восстанавливает сессию.
4. Админ видит список моделей и может искать в KB.
5. Сайт работает адаптивно, тёмная тема поддерживается, основные сценарии покрыты e2e‑тестами.

## 25. Макеты и дизайн (описательно)

* **Dialogs:** двухпанельный: слева список, справа лента. На мобиле — стек: список → диалог.
* **Operator:** канбан/таблица, таймер SLA на карточке, быстрые действия.
* **Citations:** под сообщением агента: список ссылок, иконка перехода.

---

**Примечание:** все клиентские контракты и enum должны строго соответствовать бэкенд‑спецификации. При изменении серверных схем требуется bump client‑версии и обратная совместимость в UI (feature‑flags/guards).
