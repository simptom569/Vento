# Vento — Документация проекта

## О проекте

Vento — защищённый мессенджер. FastAPI бэкенд с Clean Architecture, E2E шифрованием, поддержкой сообщений, голосовых/видео звонков, каналов и ленты постов.

---

## Стек технологий

| Слой | Технология |
|------|-----------|
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| Миграции | Alembic |
| Валидация | Pydantic v2 |
| БД | PostgreSQL 16 |
| Кэш + pub/sub | Redis |
| Очередь событий | Kafka (KRaft, без Zookeeper) |
| Хранилище файлов | MinIO (S3-совместимый) |
| Медиасервер (звонки) | LiveKit |
| DI контейнер | Dishka |
| Фоновые задачи | ARQ |
| Контейнеризация | Docker + Docker Compose |
| Мониторинг | Prometheus + Grafana |
| Python | 3.14+ |

---

## Архитектура — Clean Architecture

### Принципы

1. **Зависимости направлены только внутрь** — бизнес-логика не знает про FastAPI, SQLAlchemy, Kafka
2. **Всё контент — MESSAGE** — пост в канале = сообщение типа `post`, комментарии = сообщения в discussion-чате
3. **Всё общение — CHAT** — личка, группа, канал, secret chat — один тип с разным поведением
4. **Одна таблица вложений** — `ATTACHMENTS` для всего, `sort_order` для галереи везде
5. **Domain entities отдельно от ORM моделей** — репозиторий маппит между ними

### Слои

```
Presentation  →  Application  →  Domain  ←  Infrastructure
(FastAPI)         (Use Cases)    (Entities,   (SQLAlchemy,
                                  Ports)        Kafka, Redis)
```

---

## Файловая структура

```
project_root/
├── app/
│   ├── domain/                          # Ядро — чистый Python, без фреймворков
│   │   ├── entities/
│   │   │   ├── enums.py                 # PrivacyVisibility, TwoFAMethod, Platform, ChatType, ChatRole
│   │   │   ├── user.py                  # User, UserSettings (dataclass)
│   │   │   ├── session.py               # AuthSession(dataclass)
│   │   │   ├── chat.py                  # Chat, ChatMember
│   │   │   ├── message.py               # Message, Attachment
│   │   │   └── call.py                  # Call, CallParticipant
│   │   ├── events/
│   │   │   ├── base.py                  # DomainEvent базовый класс
│   │   │   ├── user_events.py           # UserRegistered, UserDeleted
│   │   │   ├── message_events.py        # MessageSent, MessageDeleted, MessageEdited
│   │   │   ├── chat_events.py           # ChatCreated, MemberJoined, MemberLeft
│   │   │   └── call_events.py           # CallInitiated, CallEnded, CallMissed
│   │   ├── ports/
│   │   │   ├── repositories/
│   │   │   │   ├── user_repo.py         # AbstractUserRepository (ABC)
│   │   │   │   ├── credentials_repo.py  # AbstractCredentialsRepository (ABC) — пароль отдельно
│   │   │   │   ├── chat_repo.py         # AbstractChatRepository (ABC)
│   │   │   │   ├── chat_member_repo.py         # AbstractChatMemberRepository (ABC)
│   │   │   │   ├── message_repo.py      # AbstractMessageRepository (ABC)
│   │   │   │   └── call_repo.py         # AbstractCallRepository (ABC)
│   │   │   └── services/
│   │   │       ├── event_bus.py         # AbstractEventBus (ABC)
│   │   │       ├── storage.py           # AbstractStorage (ABC)
│   │   │       └── push.py              # AbstractPushService (ABC)
│   │   └── exceptions.py                # DomainError, NotFoundError, AlreadyExistsError, ForbiddenError, ValidationError
│   │
│   ├── application/
│   │   ├── commands/
│   │   │   ├── auth/
│   │   │   │   ├── register.py          # RegisterCommand + RegisterHandler
│   │   │   │   ├── refresh_token.py     # RefreshTokenCommand + TokenPair + RefreshTokenHandler
│   │   │   │   ├── logout.py            # LogoutCommand + LogoutHandler
│   │   │   │   └── login.py             # LoginCommand + LoginHandler
│   │   │   ├── messages/
│   │   │   │   ├── send_message.py
│   │   │   │   ├── edit_message.py
│   │   │   │   └── delete_message.py
│   │   │   ├── chats/
│   │   │   │   ├── create_chat.py
│   │   │   │   ├── add_member.py
│   │   │   │   ├── change_member_role.py
│   │   │   │   ├── create_channel.py
│   │   │   │   ├── remove_member.py
│   │   │   │   ├── delete_chat.py
│   │   │   │   ├── update_channel.py
│   │   │   │   └── mute_chat.py
│   │   │   └── calls/
│   │   │       ├── initiate_call.py
│   │   │       ├── join_call.py
│   │   │       └── end_call.py
│   │   ├── queries/
│   │   │   ├── chats/
│   │   │   │   ├── get_chat_members.py
│   │   │   │   ├── get_chat.py
│   │   │   │   └── get_user_chats.py
│   │   │   ├── messages/
│   │   │   │   └── get_chat_messages.py
│   │   │   └── feed/
│   │   │       └── get_channel_feed.py
│   │   └── common/
│   │       ├── base_handler.py
│   │       └── pagination.py
│   │
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py          # импортирует все модели (нужно для alembic)
│   │   │   │   ├── base.py              # Base (DeclarativeBase) + TimestampMixin
│   │   │   │   ├── user.py              # UserModel, UserSettingsModel, UserCredentialsModel, AuthSessionModel, UserContactModel, UserKeyModel, DeviceKeyExchangeModel, EncryptedBackupModel
│   │   │   │   ├── chat.py              # ChatModel, ChatMemberModel
│   │   │   │   ├── message.py           # MessageModel, MessageRecipientsModel, AttachmentModel, MessageStatusModel, MessageReactionModel
│   │   │   │   └── call.py              # CallModel, CallParticipantModel
│   │   │   ├── repositories/
│   │   │   │   ├── user_repo.py         # UserRepository(AbstractUserRepository)
│   │   │   │   ├── credentials_repo.py  # CredentialsRepository(AbstractCredentialsRepository)
│   │   │   │   ├── chat_repo.py
│   │   │   │   ├── message_repo.py
│   │   │   │   └── call_repo.py
│   │   │   └── session.py               # engine + AsyncSessionLocal
│   │   ├── kafka/
│   │   │   ├── producer.py              # KafkaEventBus(AbstractEventBus)
│   │   │   └── consumers/
│   │   │       ├── base_consumer.py
│   │   │       ├── message_consumer.py
│   │   │       ├── notification_consumer.py
│   │   │       └── media_consumer.py
│   │   ├── redis/
│   │   │   ├── client.py
│   │   │   ├── pubsub.py
│   │   │   └── cache.py
│   │   ├── storage/
│   │   │   └── minio.py                 # MinioStorage(AbstractStorage)
│   │   └── push/
│   │       ├── base.py
│   │       └── fcm.py                   # FCMPushService(AbstractPushService)
│   │
│   ├── presentation/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routers/
│   │   │       │   ├── auth.py          # POST /auth/register
│   │   │       │   ├── users.py
│   │   │       │   ├── chats.py
│   │   │       │   ├── messages.py
│   │   │       │   ├── calls.py
│   │   │       │   └── feed.py
│   │   │       └── __init__.py
│   │   ├── websocket/
│   │   │   ├── handler.py
│   │   │   └── events.py
│   │   └── schemas/
│   │       ├── auth.py                  # RegisterRequest, RegisterResponse
│   │       ├── user.py
│   │       ├── chat.py
│   │       ├── message.py
│   │       └── call.py
│   │
│   ├── core/
│   │   ├── config.py                    # Settings (pydantic-settings)
│   │   └── security.py                  # JWT RS256, bcrypt, token utils
│   │
│   ├── container.py                     # Dishka DI-контейнер
│   └── main.py                          # create_app() + create_production_app() + app
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── unit/
│   │   └── commands/
│   │       ├── fake_repos.py            # Репозитории для теста
│   │       ├── test_login.py
│   │       ├── test_refresh_token.py
│   │       └── test_register.py
│   ├── integration/
│   │   └── repositories/
│   │       ├── test_credentials_repo.py
│   │       └── test_user_repo.py
│   ├── e2e/
│   │   ├── conftest.py                  # TestProvider, container, client fixtures
│   │   └── api/
│   │       └── test_auth.py
│   └── conftest.py                      # test_engine, test_session_factory, db_session
│
├── docker-compose.yml                   # в корне проекта
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│
├── Makefile                             # make up/down/logs-api/logs-db/migrate/test/...
├── Dockerfile                           # в корне проекта
├── alembic.ini
├── pyproject.toml
├── .env                                 # в корне проекта
└── .gitignore
```

---

## База данных — схема таблиц

### Домен 1 — Пользователи и аутентификация

#### USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | gen_random_uuid() |
| phone_number | VARCHAR(20) UNIQUE NOT NULL | Основной логин |
| username | VARCHAR(32) UNIQUE | @никнейм |
| display_name | VARCHAR(64) NOT NULL | Отображаемое имя |
| bio | TEXT | Описание профиля |
| avatar_url | TEXT | Ключ в S3/MinIO |
| last_seen_at | TIMESTAMPTZ | Последний онлайн |
| is_online | BOOLEAN DEFAULT false | Онлайн-статус |
| is_deleted | BOOLEAN DEFAULT false | Мягкое удаление |
| created_at | TIMESTAMPTZ DEFAULT now() | — |
| updated_at | TIMESTAMPTZ DEFAULT now() | — |

#### USER_SETTINGS — One-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK UNIQUE NOT NULL | → USERS |
| privacy_last_seen | ENUM(privacy_visibility) DEFAULT 'EVERYONE' | everyone/contacts/nobody |
| privacy_avatar | ENUM(privacy_visibility) DEFAULT 'EVERYONE' | — |
| privacy_phone | ENUM(privacy_visibility) DEFAULT 'CONTACTS' | — |
| notifications_enabled | BOOLEAN DEFAULT true | — |
| two_fa_method | ENUM(two_fa_method) DEFAULT 'NONE' | totp/sms/none |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

#### AUTH_SESSIONS — Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK NOT NULL | → USERS |
| device_id | VARCHAR(128) NOT NULL | Уникальный ID устройства |
| device_name | VARCHAR(128) | "iPhone 15 Pro" |
| platform | ENUM(platform) | ios/android/web/desktop |
| push_token | TEXT | FCM/APNs токен |
| refresh_token_hash | TEXT NOT NULL | SHA-256 хеш, сам токен не хранится |
| expires_at | TIMESTAMPTZ NOT NULL | Когда истекает refresh токен |
| last_used_at | TIMESTAMPTZ | Последнее использование — для детектирования кражи токена |
| ip_address | INET | IP последнего использования |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

#### USER_CONTACTS — Many-to-One → USERS (дважды)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| owner_user_id | UUID FK NOT NULL | Чей контакт |
| contact_user_id | UUID FK NOT NULL | Кто добавлен |
| custom_name | VARCHAR(64) | Своё имя для контакта |
| is_blocked | BOOLEAN DEFAULT false | Заблокирован |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

> Индекс: `uq_user_contacts_owner_contact` на `(owner_user_id, contact_user_id)`

#### USER_CREDENTIALS — One-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK UNIQUE NOT NULL | → USERS |
| password_hash | VARCHAR(255) NOT NULL | bcrypt. Хранится отдельно от профиля — domain entity про пароль не знает |

#### USER_KEYS — Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK NOT NULL | → USERS |
| device_id | VARCHAR(128) NOT NULL | Привязка к устройству (Signal Protocol) |
| key_type | VARCHAR(32) NOT NULL | signal_x3dh / device_key |
| public_key | TEXT NOT NULL | Identity Key, base64 |
| signed_pre_key | TEXT NOT NULL | Signed Pre Key + подпись, base64 |
| one_time_pre_keys | JSONB | Массив одноразовых Pre Keys |
| one_time_pre_keys_count | INTEGER DEFAULT 0 | Остаток одноразовых ключей — когда < 10 сервер просит клиент загрузить новые |
| created_at | TIMESTAMPTZ DEFAULT now() | — |
| rotated_at | TIMESTAMPTZ | Последняя ротация ключей |

> Индекс: `uq_user_keys_user_device` на `(user_id, device_id)`

#### DEVICE_KEY_EXCHANGE — Many-to-One → USERS
Временная таблица для подтверждения нового устройства со старого. Сервер — только почтальон, криптография на клиенте.

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK NOT NULL | → USERS |
| requesting_device_id | VARCHAR(128) NOT NULL | Новое устройство которое хочет войти |
| approving_device_id | VARCHAR(128) | Старое устройство которое подтверждает (NULL если через recovery key) |
| encrypted_blob | TEXT | Recovery key зашифрованный публичным ключом нового устройства |
| status | VARCHAR(16) NOT NULL | pending/approved/rejected/expired |
| expires_at | TIMESTAMPTZ NOT NULL | TTL 10 минут |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

#### ENCRYPTED_BACKUPS — Many-to-One → USERS
Зашифрованный бэкап истории для восстановления на новом устройстве. Сервер не может расшифровать — ключ знает только пользователь (recovery key).

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| user_id | UUID FK NOT NULL | → USERS |
| encrypted_data | TEXT NOT NULL | История зашифрованная recovery key пользователя |
| version | INTEGER DEFAULT 1 | Версия бэкапа |
| size_bytes | BIGINT | Размер зашифрованных данных |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

---

### Домен 2 — Чаты и сообщения

#### CHATS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| type | VARCHAR(16) NOT NULL | private/group/secret/channel |
| title | VARCHAR(128) | NULL для private |
| username | VARCHAR(32) UNIQUE | @адрес для channel/публичных групп |
| avatar_url | TEXT | — |
| created_by | UUID FK → USERS | Кто создал |
| is_public | BOOLEAN DEFAULT false | Ищется в поиске |
| is_verified | BOOLEAN DEFAULT false | Верифицированный (галочка) |
| is_encrypted | BOOLEAN DEFAULT true | E2E шифрование |
| member_count | INTEGER DEFAULT 0 | Денормализованный счётчик |
| discussion_chat_id | UUID FK → CHATS NULL | Для channel: чат комментариев (самореференс) |
| created_at | TIMESTAMPTZ DEFAULT now() | — |
| updated_at | TIMESTAMPTZ DEFAULT now() | Обновляется при новом сообщении |

#### CHAT_MEMBERS — Many-to-Many (CHATS × USERS)
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| chat_id | UUID FK NOT NULL | → CHATS |
| user_id | UUID FK NOT NULL | → USERS |
| role | VARCHAR(16) DEFAULT 'member' | owner/admin/member/subscriber |
| joined_at | TIMESTAMPTZ DEFAULT now() | — |
| muted_until | TIMESTAMPTZ NULL | Уведомления заглушены до |
| is_archived | BOOLEAN DEFAULT false | Скрыт в архив |
| last_read_message_seq | INTEGER DEFAULT 0 | Для счётчика непрочитанных |
| deleted_at | TIMESTAMPTZ NULL | момент когда пользователь "удалил" чат у себя (soft delete). Если None — чат активен |
| deleted_before_message_seq | INTEGER DEFAULT 0 | порядковый номер последнего сообщения на момент удаления. Нужен чтобы не показывать старые сообщения после восстановления чата |

> Индекс: `uq_chat_members_chat_user` на `(chat_id, user_id)`

#### MESSAGES — Many-to-One → CHATS, Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| chat_id | UUID FK NOT NULL | → CHATS |
| sender_id | UUID FK NOT NULL | → USERS |
| reply_to_id | UUID FK NULL | → MESSAGES (самореференс) |
| type | VARCHAR(16) NOT NULL | text/image/video/audio/voice/file/sticker/system/post |
| encrypted_payload | TEXT NULL | AES-GCM base64. Для Secret Chats — один блоб. Для обычных чатов — NULL, блобы в MESSAGE_RECIPIENTS |
| is_edited | BOOLEAN DEFAULT false | — |
| is_deleted | BOOLEAN DEFAULT false | Мягкое удаление |
| sent_at | TIMESTAMPTZ DEFAULT now() | — |
| edited_at | TIMESTAMPTZ | — |
| sequence_number | INTEGER NOT NULL | Монотонный номер в рамках чата |

> IV (Initialization Vector) хранится внутри `encrypted_payload` — AES-GCM включает его в структуру блоба. Отдельное поле не нужно.
> Для поста в канале: type = 'post', FEED_POSTS ссылается на этот MESSAGE

#### ATTACHMENTS — Many-to-One → MESSAGES
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| message_id | UUID FK NOT NULL | → MESSAGES |
| type | VARCHAR(16) NOT NULL | image/video/audio/voice/file |
| storage_key | TEXT NOT NULL | Путь в S3/MinIO |
| mime_type | VARCHAR(64) | image/jpeg, video/mp4 и т.д. |
| file_size | BIGINT | Байты |
| duration_sec | INTEGER | Для аудио/видео |
| width | INTEGER | Пиксели |
| height | INTEGER | Пиксели |
| thumbnail_key | TEXT | Превью в хранилище |
| sort_order | SMALLINT DEFAULT 0 | Порядок в галерее |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

#### MESSAGE_RECIPIENTS — Many-to-One → MESSAGES, Many-to-One → USERS
Multi-Device E2E — каждое сообщение шифруется отдельно для каждого устройства получателя. Сервер видит только зашифрованные блобы.

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| message_id | UUID FK NOT NULL | → MESSAGES |
| user_id | UUID FK NOT NULL | → USERS |
| device_id | VARCHAR(128) NOT NULL | Конкретное устройство получателя |
| encrypted_payload | TEXT NOT NULL | Блоб зашифрованный публичным ключом этого устройства |
| is_delivered | BOOLEAN DEFAULT false | Доставлено на устройство |

> Индекс: `uq_message_recipients` на `(message_id, device_id)`
> Используется только для обычных чатов (PRIVATE, GROUP). Secret Chats используют `encrypted_payload` в MESSAGES напрямую.

#### MESSAGE_STATUS — Many-to-One → MESSAGES, Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| message_id | UUID FK NOT NULL | → MESSAGES |
| user_id | UUID FK NOT NULL | → USERS |
| status | VARCHAR(16) NOT NULL | sent/delivered/read |
| updated_at | TIMESTAMPTZ DEFAULT now() | — |

> Индекс: `uq_message_status_message_user` на `(message_id, user_id)`

#### MESSAGE_REACTIONS — Many-to-One → MESSAGES, Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| message_id | UUID FK NOT NULL | → MESSAGES |
| user_id | UUID FK NOT NULL | → USERS |
| emoji | VARCHAR(8) NOT NULL | Unicode эмодзи |
| created_at | TIMESTAMPTZ DEFAULT now() | — |

> Индекс: `uq_message_reactions_message_user_emoji` на `(message_id, user_id, emoji)`

---

### Домен 3 — Звонки

#### CALLS — Many-to-One → CHATS, Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| chat_id | UUID FK NOT NULL | → CHATS |
| initiator_id | UUID FK NOT NULL | → USERS |
| type | VARCHAR(16) NOT NULL | audio/video |
| status | VARCHAR(16) NOT NULL | ringing/active/ended/missed/rejected |
| webrtc_room_id | VARCHAR(128) | ID комнаты на LiveKit/Mediasoup |
| started_at | TIMESTAMPTZ | Когда принят |
| ended_at | TIMESTAMPTZ | Когда завершён |
| duration_sec | INTEGER | Итоговая длительность |

#### CALL_PARTICIPANTS — Many-to-One → CALLS, Many-to-One → USERS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| call_id | UUID FK NOT NULL | → CALLS |
| user_id | UUID FK NOT NULL | → USERS |
| status | VARCHAR(16) NOT NULL | invited/joined/left/declined |
| joined_at | TIMESTAMPTZ | — |
| left_at | TIMESTAMPTZ | — |
| camera_on | BOOLEAN DEFAULT false | — |
| mic_on | BOOLEAN DEFAULT true | — |
| screen_sharing | BOOLEAN DEFAULT false | — |

---

### Домен 4 — Каналы и лента

#### FEED_POSTS — One-to-One → MESSAGES, Many-to-One → CHATS
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | — |
| message_id | UUID FK UNIQUE NOT NULL | → MESSAGES. Контент и медиа живут там |
| channel_id | UUID FK NOT NULL | → CHATS (type = 'channel') |
| is_pinned | BOOLEAN DEFAULT false | Закреплён |
| views_count | INTEGER DEFAULT 0 | Денормализованный счётчик |
| forwards_count | INTEGER DEFAULT 0 | Сколько раз переслали |
| published_at | TIMESTAMPTZ DEFAULT now() | — |

---

### PostgreSQL ENUM типы
| Имя | Значения |
|-----|---------|
| privacy_visibility | EVERYONE, CONTACTS, NOBODY |
| two_fa_method | TOTP, SMS, NONE |
| platform | IOS, ANDROID, WEB, DESKTOP |
| chat_type | PRIVATE, GROUP, SECRET, CHANNEL |
| chat_member_role | OWNER, ADMIN, MEMBER, SUBSCRIBER |

---

## Что уже сделано ✅

### Полный путь для User/Register

1. **domain/entities/user.py** — `User`, `UserSettings` dataclass с бизнес-методами (`go_online`, `go_offline`, `update_profile`)
2. **domain/entities/enums.py** — все enum типы
3. **domain/exceptions.py** — `DomainError`, `NotFoundError`, `AlreadyExistsError`, `ForbiddenError`, `ValidationError`
4. **domain/ports/repositories/user_repo.py** — `AbstractUserRepository` (ABC)
5. **application/commands/auth/register.py** — `RegisterCommand` + `RegisterHandler`
6. **tests/unit/commands/test_register.py** — 4 unit теста ✅
7. **infrastructure/db/models/base.py** — `Base` + `TimestampMixin`
8. **infrastructure/db/models/user.py** — все 5 моделей юзера
9. **alembic миграции** — таблицы созданы в БД
10. **infrastructure/db/repositories/user_repo.py** — с `joinedload` для settings
11. **infrastructure/db/session.py** — `engine` + `AsyncSessionLocal`
12. **tests/integration/repositories/test_user_repo.py** — 7 integration тестов ✅
13. **app/container.py** — Dishka DI-контейнер с `get_session_factory`
14. **app/core/config.py** — `Settings` (pydantic-settings)
15. **app/main.py** — `create_app()` + `create_production_app()` + `app`
16. **presentation/schemas/auth.py** — `RegisterRequest`, `RegisterResponse`
17. **presentation/api/v1/routers/auth.py** — `POST /api/v1/auth/register` с `FromDishka[RegisterHandler]`
18. **tests/conftest.py** — `test_engine`, `test_session_factory`, `db_session`
19. **tests/e2e/conftest.py** — `TestProvider`, `container`, `client`
20. **tests/e2e/api/test_auth.py** — 3 e2e теста ✅
21. **Dockerfile** — в корне проекта
22. **docker-compose.yml** — в корне проекта, `.env` рядом
23. **Makefile** — `make up/down/logs-api/logs-db/migrate/test/test-unit/test-integration/test-e2e`

---

## Важные детали реализации

### app/main.py — два варианта приложения
```python
def create_app() -> FastAPI:
    """Чистое приложение без контейнера — используется в тестах"""
    app = FastAPI(...)
    app.include_router(auth_router, prefix="/api/v1")
    return app

def create_production_app() -> FastAPI:
    """Продакшн — с Dishka контейнером"""
    app = create_app()
    setup_dishka(container, app=app)
    return app

app = create_production_app()  # uvicorn использует этот объект
```

Разделение нужно потому что `setup_dishka` нельзя вызвать дважды на одно приложение. В тестах каждый тест создаёт свежее приложение через `create_app()`.

### app/container.py — Dishka провайдер
```python
class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings: ...

    @provide(scope=Scope.APP)
    def get_engine(self, settings: Settings) -> AsyncEngine: ...

    @provide(scope=Scope.APP)
    def get_session_factory(self, engine: AsyncEngine) -> async_sessionmaker: ...

    @provide(scope=Scope.REQUEST)
    async def get_session(self, factory: async_sessionmaker) -> AsyncIterator[AsyncSession]: ...

    @provide(scope=Scope.REQUEST)
    def get_user_repo(self, session: AsyncSession) -> AbstractUserRepository: ...

    @provide(scope=Scope.REQUEST)
    def get_register_handler(self, user_repo: AbstractUserRepository) -> RegisterHandler: ...
```

### presentation/api/v1/routers/auth.py — синтаксис Dishka
```python
@router.post("/register", response_model=RegisterResponse)
@inject
async def register(
    body: RegisterRequest,
    handler: FromDishka[RegisterHandler],  # ← правильный синтаксис (не Annotated)
):
    ...
```

### tests/ — структура fixtures
```
tests/conftest.py         # test_engine, test_session_factory, db_session (для всех тестов)
tests/e2e/conftest.py     # TestProvider, container, client (только для e2e)
```

`TestProvider` в e2e содержит все три зависимости: `get_session`, `get_user_repo`, `get_register_handler`.

---

## Что делать дальше

### Следующий приоритет — Auth завершить

```
1. core/security.py                  — JWT RS256 (access 15min + refresh 30d)
2. domain/ports/repositories/
   credentials_repo.py               — AbstractCredentialsRepository (ABC)
3. infrastructure/db/models/user.py  — UserCredentialsModel
4. infrastructure/db/repositories/
   credentials_repo.py               — реализация
5. login use case                    — проверка пароля (bcrypt), выдача токенов
6. refresh token use case            — ротация refresh токена
7. get_current_user Depends          — для защищённых роутеров
8. GET /users/me                     — первый защищённый эндпоинт
9. Миграция                          — user_credentials + auth_sessions изменения
```

### Потом — Чаты и сообщения

```
10. ORM модели chat.py, message.py, call.py
11. Миграции для новых таблиц
12. Репозитории чатов и сообщений
13. Use cases: create_chat, send_message
14. WebSocket handler                — real-time через Redis pub/sub
```

---

## Ключевые архитектурные решения

### Почему Clean Architecture
- Use cases тестируются без БД (FakeRepository)
- Можно поменять PostgreSQL/Kafka не трогая бизнес-логику
- Каждый хендлер делает одну вещь (Single Responsibility)

### Почему domain entities отдельно от ORM
- ORM модели знают про БД, domain entities — нет
- Репозиторий — переводчик между слоями
- Без этого бизнес-логика зависит от SQLAlchemy

### Почему joinedload обязателен в async
- Lazy loading в async SQLAlchemy невозможен без await
- `lazy="raise"` на relationship защищает от случайного lazy loading
- Все связанные данные грузятся явно в репозитории

### Почему FEED_POSTS → MESSAGES
- Пост в канале = MESSAGE с type='post'
- Комментарии = обычные сообщения в discussion_chat
- Медиа поста = ATTACHMENTS как у любого сообщения
- Один механизм для всего, нет дублирования логики

### Почему нет отдельных CHANNELS и CHANNEL_SUBSCRIBERS
- Канал = CHAT с type='channel'
- Подписка = CHAT_MEMBERS с role='subscriber'
- Телеграм устроен так же

### Архитектура безопасности

#### JWT — RS256
- Приватный ключ только на auth-сервисе
- Все микросервисы верифицируют токен публичным ключом — никогда не видят приватный
- Access токен: 15 минут
- Refresh токен: 30 дней, случайная строка (`secrets.token_urlsafe`), в БД хранится SHA-256 хеш

#### Refresh токен — ротация с детектированием кражи
- При каждом `/auth/refresh` старый токен инвалидируется, выдаётся новый
- Если старый токен использован повторно — признак кражи, все сессии пользователя инвалидируются
- `last_used_at` в AUTH_SESSIONS позволяет отследить подозрительную активность

#### Пароль — отдельная таблица
- `USER_CREDENTIALS` отдельно от `USERS` — domain entity про пароль не знает
- `AbstractCredentialsRepository` в domain/ports — отдельный порт, не смешивается с UserRepository
- bcrypt — намеренно медленный алгоритм, брутфорс нецелесообразен

#### E2E шифрование сообщений — два режима
**Обычные чаты (PRIVATE, GROUP)** — Multi-Device E2E:
- Каждое сообщение шифруется отдельно для каждого устройства получателя (Signal Protocol X3DH + Double Ratchet)
- Блобы хранятся в `MESSAGE_RECIPIENTS` — один на устройство
- Сервер видит зашифрованные блобы, не может расшифровать
- История доступна на всех устройствах ✅

**Secret Chats (SECRET)** — классический Signal Protocol:
- Одно устройство, один блоб в `MESSAGES.encrypted_payload`
- Максимальная защита, история не синхронизируется

#### Ключи устройств — Signal Protocol
- Каждое устройство имеет свой независимый набор ключей в `USER_KEYS`
- Identity Key (долгосрочный) + Signed PreKey (еженедельно) + One-Time PreKeys (одноразовые)
- One-Time PreKeys добавляют уникальную энтропию каждой сессии — без них все сессии за неделю криптографически связаны
- Когда остаток < 10 — сервер уведомляет клиент (`one_time_pre_keys_count`)
- Fallback без One-Time PreKey возможен, но нежелателен

#### Новое устройство — два пути
1. **Подтверждение со старого устройства** — старое устройство шифрует recovery key публичным ключом нового, передаёт через `DEVICE_KEY_EXCHANGE`. Сервер не видит recovery key.
2. **Recovery key** — строка сохранённая при регистрации (как seed-фраза). Расшифровывает `ENCRYPTED_BACKUPS` локально на новом устройстве.

#### Звонки — LiveKit + SFrame
- LiveKit поддерживает E2E через SFrame (Secure Frame)
- Ключи генерируются на клиентах, сервер видит только зашифрованные медиафреймы

---

## Конфигурация

### .env (в корне проекта)
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DB=Vento
```

### pyproject.toml — pytest секция
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

### Makefile команды
```bash
make up              # поднять контейнеры
make down            # остановить контейнеры
make logs-api        # логи api контейнера
make logs-db         # логи postgres контейнера
make migrate         # alembic upgrade head
make test            # все тесты
make test-unit       # только unit
make test-integration # только integration
make test-e2e        # только e2e
```

### Прямые команды (без make)
```bash
# поднять БД
sudo docker compose up -d postgres

# миграции
poetry run alembic upgrade head

# запуск приложения
poetry run uvicorn app.main:app --reload

# тесты
poetry run pytest -v
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
poetry run pytest tests/e2e/ -v
```

---

## Зависимости (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = ">=3.14"
fastapi = {extras = ["standard"], version = ">=0.136.1,<0.137.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.49"}
alembic = "^1.18.4"
asyncpg = "^0.31.0"
pydantic-settings = "^2.14.0"
dishka = "^1.10.1"
uvicorn = "^0.46.0"
python-jose = {extras = ["cryptography"], version = "^3.5.0"}
bcrypt = "^5.0.0"

[tool.poetry.group.dev.dependencies]
pytest = ">=9.0.3,<10.0.0"
pytest-asyncio = "^1.3.0"
httpx = "^0.28.1"
```
