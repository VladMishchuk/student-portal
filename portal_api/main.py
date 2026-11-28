"""Застосунок FastAPI: ті самі дані, що й у сайті Django, для інших систем."""

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from student_portal.group import Group

from . import orm
from .schemas import (
    GradeIn,
    GradeOut,
    GradeUpdate,
    RankingItem,
    StudentOut,
    StudentPage,
)
from .settings import Settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="Ключ з PORTAL_API_KEY",
)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Сесія бази даних на один запит; закривається після відповіді."""
    async with request.app.state.sessionmaker() as session:
        yield session


async def check_api_key(
    request: Request,
    key: Annotated[str, Depends(api_key_header)],
) -> None:
    """Перевіряє заголовок X-API-Key у постійному часі."""
    expected = request.app.state.settings.api_key.get_secret_value()
    if not secrets.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неправильний ключ API")


SessionDep = Annotated[AsyncSession, Depends(get_session)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Студента немає"}}
GRADE_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"description": "Оцінку не знайдено"}
}

router = APIRouter(dependencies=[Depends(check_api_key)])


@router.get("/students", tags=["students"])
async def list_students(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StudentPage:
    """Студенти з оцінками і середнім балом, сторінками по limit."""
    count = await session.scalar(select(func.count()).select_from(orm.Student))
    students = await session.scalars(
        select(orm.Student)
        .options(selectinload(orm.Student.grades))
        .order_by(orm.Student.id)
        .limit(limit)
        .offset(offset)
    )
    items = [StudentOut.model_validate(s) for s in students]
    return StudentPage(count=count or 0, items=items)


async def find_student(session: AsyncSession, student_id: int) -> orm.Student:
    """Знаходить студента з оцінками або повертає 404."""
    student = await session.get(
        orm.Student,
        student_id,
        options=[selectinload(orm.Student.grades)],
    )
    if student is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Студента з id={student_id} немає",
        )
    return student


@router.get("/students/{student_id}", tags=["students"], responses=NOT_FOUND)
async def get_student(student_id: int, session: SessionDep) -> StudentOut:
    """Студент з оцінками."""
    return StudentOut.model_validate(await find_student(session, student_id))


@router.post(
    "/students/{student_id}/grades",
    tags=["grades"],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
async def add_grade(
    student_id: int,
    grade: GradeIn,
    session: SessionDep,
) -> GradeOut:
    """Нова оцінка студента; літеру ECTS обчислює ядро."""
    await find_student(session, student_id)
    record = orm.Grade(student_id=student_id, **grade.model_dump())
    session.add(record)
    await session.commit()
    return GradeOut.model_validate(record)


@router.patch(
    "/grades/{grade_id}",
    tags=["grades"],
    responses=GRADE_NOT_FOUND,
)
async def update_grade(
    grade_id: int,
    grade: GradeUpdate,
    session: SessionDep,
) -> GradeOut:
    """Часткове оновлення оцінки; оновлюються лише передані поля."""
    record = await session.get(orm.Grade, grade_id)
    if record is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Оцінку з id={grade_id} не знайдено",
        )
    for field, value in grade.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await session.commit()
    return GradeOut.model_validate(record)


@router.get("/ranking", tags=["students"])
async def get_ranking(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[RankingItem]:
    """Рейтинг студентів за правилами ядра (Group.ranking)."""
    students = await session.scalars(
        select(orm.Student).options(selectinload(orm.Student.grades))
    )
    core_group = Group("усі студенти")
    for student in students:
        core_group.add(orm.to_core(student))

    return [
        RankingItem(
            place=place,
            id=student.id,
            full_name=student.full_name,
            average=student.average(),
        )
        for place, student in enumerate(core_group.ranking()[:limit], start=1)
    ]


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
    app.include_router(router)
    return app


app = create_app()
