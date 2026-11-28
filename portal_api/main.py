"""Застосунок FastAPI: ті самі дані, що й у сайті Django, для інших систем."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Створює застосунок; без settings налаштування читаються під час запуску."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = config = settings or Settings()
        engine = create_async_engine(config.database_url, echo=config.echo_sql)
        app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Student Portal API",
        version="0.10.0",
        summary="Студенти й оцінки для інших систем університету",
        lifespan=lifespan,
    )
    return app


app = create_app()
