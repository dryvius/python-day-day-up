"""Thin HTTP adapter for Todo operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from todo_api.database import get_db
from todo_api.deps import require_api_key
from todo_api.schemas import TodoCreate, TodoRead, TodoUpdate
from todo_api.services import todo_service

router = APIRouter(
    prefix="/v1/todos",
    tags=["todos"],
    dependencies=[Depends(require_api_key)],
)
DatabaseSession = Annotated[Session, Depends(get_db)]


def _not_found(error: todo_service.TodoNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, session: DatabaseSession) -> TodoRead:
    return TodoRead.model_validate(todo_service.create_todo(session, payload))


@router.get("", response_model=list[TodoRead])
def list_todos(
    session: DatabaseSession,
    done: Annotated[bool | None, Query()] = None,
) -> list[TodoRead]:
    return [TodoRead.model_validate(todo) for todo in todo_service.list_todos(session, done)]


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo(todo_id: int, session: DatabaseSession) -> TodoRead:
    try:
        return TodoRead.model_validate(todo_service.get_todo(session, todo_id))
    except todo_service.TodoNotFoundError as error:
        raise _not_found(error) from error


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, payload: TodoUpdate, session: DatabaseSession) -> TodoRead:
    try:
        return TodoRead.model_validate(todo_service.update_todo(session, todo_id, payload))
    except todo_service.TodoNotFoundError as error:
        raise _not_found(error) from error


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: DatabaseSession) -> Response:
    try:
        todo_service.delete_todo(session, todo_id)
    except todo_service.TodoNotFoundError as error:
        raise _not_found(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
