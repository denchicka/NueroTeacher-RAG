# NeuroTeacher RAG

> Готовый прототип *нейро‑сотрудника/преподавателя* для курсов **Roblox / Python / WEB**, который ищет ответы **только** в загруженных документах (RAG), умеет модерировать вход, логгировать ответы и считать стоимость токенов. Интерфейс — **Gradio** с двумя режимами: загрузка **Google Docs** или **.docx**.

## Содержание
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Политика безопасности](#политика-безопасности)
- [Как пользоваться (UI)](#как-пользоваться-ui)
- [Структура проекта (рекомендуемая)](#структура-проекта-рекомендуемая)
- [Known Issues](#known-issues)
- [План модернизации](#план-модернизации)
- [Лицензия](#лицензия)

## Возможности

- **RAG‑поиск**: OpenAI Embeddings -> **Chroma** (dense) + **BM25**; объединение через **EnsembleRetriever** и перефраз запроса через **MultiQueryRetriever** (MMR, фильтры по курсу).
- **Две LLM**: OpenAI (`ChatOpenAI`) и **GigaChat** (через `langchain_gigachat` и прямой SDK).
- **Модерация и безопасность**: OpenAI Moderation + собственная политика `safety_policy.yaml` с правилами и авто‑заменами.
- **Трассировка**: OpenInference + **Arize Phoenix** (OTLP), опционально с **ngrok** для внешнего UI.
- **Gradio‑интерфейс**: режим **Google Docs** (по ссылке) или **.docx** (загрузка файла); лог и стоимость в аккордеоне.
- **Подсчёт токенов/стоимости**, логгирование шагов пайплайна.
- **Поддержка структурированного .docx**: извлечение по заголовкам `Heading 1–3` / `Заголовок 1–3` и разбиение на чанки.

## Архитектура

```
Пользовательский запрос -> Gradio UI
            -> Модерация (OpenAI Moderation + safety_policy.yaml)
            -> Перефраз запроса (MultiQueryRetriever)
            -> Поиск по базе знаний:
                 - Dense: OpenAI Embeddings -> Chroma (MMR, k=5, fetch_k=30)
                 - Sparse: BM25 (rank_bm25)
               -> EnsembleRetriever (веса dense/sparse)
            -> LLM (GigaChat / OpenAI) с системным промптом курса
            -> Ответ + логи + стоимость
            -> Трассировка (OpenInference -> OTLP -> Arize Phoenix)
```

## Быстрый старт

### 1) Установка

Python 3.10+
```bash
python -m venv .venv && source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -U pip
pip install -U \
langchain langchain-openai langchain-community langchain-chroma langchain-gigachat \
chromadb langchain-text-splitters python-docx gradio requests python-dotenv openai
```

### 2) Ключи и конфиги

Создайте файл `.env` (или экспортируйте переменные окружения любым удобным способом):

```bash
export OPENAI_API_KEY="sk-..."
export GIGACHAT_AUTHORIZATION="base64(client_id:client_secret)"     # см. доки Sber GigaChat
export NGROK_AUTH_TOKEN="..."                                       # опционально, для Phoenix UI снаружи
```

### 3) Phoenix (опционально)

Локально:
```bash
phoenix serve --host 127.0.0.1 --port 6006
```

С внешним доступом (ngrok):
```bash
ngrok config add-authtoken $NGROK_AUTH_TOKEN
ngrok http 6006
# получите внешний URL и откройте Phoenix UI
```

### 4) Запуск (локально)

```python
# ключи

# OpenAi
export OPENAI_API_KEY="sk-..." # PowerShell: $env:OPENAI_API_KEY="sk-..."

# GigaChat (вариант 1 - готовая base64)
# export GIGACHAT_AUTHORIZATION="base64(client_id:client_secret)"

# GigaChat (вариант 2 - пусть код соберёт base64 сам)
export GIGACHAT_CLIENT_ID="..."
export GIGACHAT_CLIENT_SECRET="..."

# scope по умолчанию: GIGACHAT_API_PERS (можно сменить)
export GIGACHAT_SCOPE="GIGACHAT_API_PERS"

# SSL (для корпоративных сетей/MITM)
# export GIGACHAT_VERIFY_SSL=false
# export GIGACHAT_CA_BUNDLE=/path/to/cacert.pem


# путь к индексу (опционально)
export CHROMA_DIR=./data/chroma


# запуск UI
python apps/gradio_app/app.py
```

### 4.1 Запуск (Colab)

```python
!pip install -U langchain langchain-openai langchain-community langchain-chroma langchain-gigachat \
chromadb langchain-text-splitters python-docx gradio requests python-dotenv openai


import os, getpass, base64, sys, pathlib, importlib.util
os.environ["OPENAI_API_KEY"] = getpass.getpass("OPENAI API Key: ")


# GigaChat
client_id = getpass.getpass("GigaChat CLIENT_ID: ")
client_secret = getpass.getpass("GigaChat CLIENT_SECRET: ")
os.environ["GIGACHAT_AUTHORIZATION"] = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"

# Если у вас MITM/корп‑прокси:
os.environ["GIGACHAT_VERIFY_SSL"] = "false" # или укажите CA: os.environ["GIGACHAT_CA_BUNDLE"] = "/content/certs/cacert.pem"


os.environ["CHROMA_DIR"] = "./data/chroma"


ROOT = pathlib.Path(".").resolve()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("app", "apps/gradio_app/app.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


demo = mod.build_app(persist_path=os.getenv("CHROMA_DIR"))
demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
```

## Переменные окружения

- `OPENAI_API_KEY` — ключ OpenAI.
- `GIGACHAT_AUTHORIZATION` — `base64(client_id:client_secret)` для OAuth GigaChat (`scope=GIGACHAT_API_PERS`).  
- `NGROK_AUTH_TOKEN` — токен для создания внешнего туннеля (опционально).

## Политика безопасности

В проекте используется файл `safety_policy.yaml` с настройками модерации и авто‑замен терминов. Минимальный пример:

```yaml
meta:
  version: 1.0.0
  owner: safety-team
thresholds:
  moderation:
    model: omni-moderation-latest
danger:
  real_world_markers:
    - "\bв\s+реал\w+\b"
    - "\birl\b"
replace:
  terms:
    - from: "\b(gun|пистолет|оружие)\b"
      to: "бластер (игровой инструмент)"
responses:
  blocked_input: "⛔ Запрос заблокирован политикой безопасности."
```

## Как пользоваться (UI)

1. Выберите режим источника: **“📄 Google Docs”** или **“📎 Загрузка .docx”**.  
2. Для Google Docs: укажите **курс**, **название**, **системный промпт** и **ссылку**, нажмите **“Обучить”**.  
   Для .docx: загрузите файл, при необходимости задайте промпт, нажмите **“Загрузить”**.  
3. Дождитесь статуса в **Progress/Log** (кнопка “Очистить память” сбрасывает индексы/состояние).  
4. Введите вопрос в поле **“Запрос к LLM”** и нажмите **“Запрос к модели”**.  
5. Ответ появится вверху; подробные логи и стоимость - в аккордеоне.

## Структура проекта (рекомендуемая)

```
.
├─ apps/
│ └─ gradio_app/
│ └─ app.py # весь UI + wiring
├─ neuroteacher/
│ ├─ core/
│ │ ├─ contracts.py # интерфейсы LLM/Embeddings/Retriever/VectorStore
│ │ └─ types.py # Doc
│ ├─ adapters/
│ │ ├─ docs/
│ │ │ ├─ docx_loader.py # .docx → чанки
│ │ │ └─ gdocs_loader.py # GDocs → чанки
│ │ ├─ llm/
│ │ │ ├─ openai_llm.py
│ │ │ └─ gigachat_llm.py # с credentials/scope + SSL toggles
│ │ ├─ embeds/
│ │ │ └─ openai_embeds.py
│ │ ├─ vectorstores/
│ │ │ └─ chroma_store.py
│ │ └─ retrievers/
│ │ └─ dense_retriever.py # совместим с invoke/get_relevant_documents
│ ├─ services/
│ │ ├─ indexing_service.py # загрузка источников + санитайз
│ │ ├─ rag_service.py # индексация + ответ
│ │ └─ safety_service.py # модерация/политика
│ └─ utils/
│ ├─ logger.py # консоль + буфер логов для UI
│ └─ config.py # (опционально) загрузка списков моделей
├─ config/
│ └─ models.toml # (опционально) список моделей по провайдерам
├─ safety_policy.yaml
└─ README.md
```

## Known Issues

- Иногда фильтрация — **слишком жёсткая** (пример с вопросом про "Войну и Мир" у Python‑преподавателя).
- Модерация может **пропустить неподходящий** вопрос (пример по WEB‑разработке).
- Локально проект может **не запуститься** из‑за OpenAI‑моделей (без `proxy/VPN`).
- **Конфликт Gradio и Phoenix**: иногда нужно перезапускать ячейки с Phoenix, убивая старый процесс.
- Некоторые чанки приходят **без `score`** (не все ретриверы возвращают оценки).
- Трассировка иногда срабатывает на **пустой запрос** (EnsembleRetriever обрабатывает пустой input).

## План модернизации

- Добавить **пересчёт стоимости в рублях** по текущему курсу.
- Собрать **веб‑интерфейс** на `React/VanillaJS` (вместо чистого Gradio) и/или вынести фронтенд отдельно.
- Поднять **REST API** на `FastAPI`.
- Сделать **Telegram‑бота**.
- Добавить поддержку загрузки **скриншотов**.
- Улучшить **структурирование .docx** (заголовки, секции, метаданные).

## Лицензия

Этот проект создан для образовательных и демонстрационных целей.

## Обратная связь

Если у Вас есть пожелания или вопросы, Вы можете связаться в личных сообщениях в мессенджере [Telegram](t.me/denchicka213)