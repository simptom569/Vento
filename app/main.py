from contextlib import asynccontextmanager

from fastapi import FastAPI
from dishka.integrations.fastapi import setup_dishka

from app.container import container
from app.presentation.api.v1.routers.auth import router as auth_router
from app.presentation.api.v1.routers.users import router as users_router
from app.presentation.api.v1.routers.chats import router as chats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Сервер запускается...')
    yield
    print('Сервер остановлен.')


def create_app() -> FastAPI:
    app = FastAPI(
        title='Vento',
        version='1.0.0',
        description='API for messenger',
        lifespan=lifespan,
    )
    
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(chats_router, prefix="/api/v1")
    
    return app


def create_production_app() -> FastAPI:
    app = create_app()
    setup_dishka(container, app=app)
    return app


# uvicorn использует этот объект
app = create_production_app()