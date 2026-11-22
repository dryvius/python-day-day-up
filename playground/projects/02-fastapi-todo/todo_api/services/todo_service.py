"""Todo business operations isolated from HTTP routing."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from todo_api.models import Todo
from todo_api.schemas import TodoCreate, TodoUpdate


class TodoNotFoundError(Exception):
    def __init__(self, todo_id: int) -> None:
        super().__init__(f"Todo {todo_id} 不存在")


def create_todo(session: Session, payload: TodoCreate) -> Todo:
    todo = Todo(**payload.model_dump())
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def list_todos(session: Session, done: bool | None = None) -> list[Todo]:
    statement = select(Todo).order_by(Todo.id)
    if done is not None:
        statement = statement.where(Todo.done.is_(done))
    return list(session.scalars(statement))


def get_todo(session: Session, todo_id: int) -> Todo:
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise TodoNotFoundError(todo_id)
    return todo


def update_todo(session: Session, todo_id: int, payload: TodoUpdate) -> Todo:
    todo = get_todo(session, todo_id)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(todo, field, value)
    session.commit()
    session.refresh(todo)
    return todo


def delete_todo(session: Session, todo_id: int) -> None:
    todo = get_todo(session, todo_id)
    session.delete(todo)
    session.commit()
