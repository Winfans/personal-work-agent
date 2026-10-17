from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.routes.notes import get_note_service
from src.main import app
from src.schemas.note import NoteCreate, NoteUpdate


class FakeNoteService:
    def __init__(self) -> None:
        self.notes: dict[int, SimpleNamespace] = {}
        self.next_id = 1

    async def list(self, offset: int, limit: int) -> list[SimpleNamespace]:
        return list(self.notes.values())[offset:offset + limit]

    async def get(self, note_id: int) -> SimpleNamespace | None:
        return self.notes.get(note_id)

    async def create(self, payload: NoteCreate) -> SimpleNamespace:
        now = datetime(2026, 10, 15, 12, 0, 0)
        note = SimpleNamespace(
            id=self.next_id,
            title=payload.title,
            content=payload.content,
            created_at=now,
            updated_at=now,
        )
        self.notes[note.id] = note
        self.next_id += 1
        return note

    async def update(self, note: SimpleNamespace, payload: NoteUpdate) -> SimpleNamespace:
        if payload.title is not None:
            note.title = payload.title
        if payload.content is not None:
            note.content = payload.content
        return note

    async def delete(self, note: SimpleNamespace) -> None:
        self.notes.pop(note.id)


client = TestClient(app)


def test_note_crud() -> None:
    service = FakeNoteService()
    app.dependency_overrides[get_note_service] = lambda: service
    try:
        created = client.post(
            "/api/v1/notes",
            json={"title": "今日计划", "content": "完成笔记 API"},
        )
        assert created.status_code == 201
        assert created.json()["code"] == 0
        assert created.json()["message"] == "OK"
        assert created.json()["data"]["id"] == 1

        listed = client.get("/api/v1/notes")
        assert listed.status_code == 200
        assert listed.json()["code"] == 0
        assert listed.json()["message"] == "OK"
        assert len(listed.json()["data"]) == 1

        fetched = client.get("/api/v1/notes/1")
        assert fetched.status_code == 200
        assert fetched.json()["data"]["title"] == "今日计划"

        updated = client.put("/api/v1/notes/1", json={"content": "已经完成"})
        assert updated.status_code == 200
        assert updated.json()["data"]["content"] == "已经完成"

        deleted = client.delete("/api/v1/notes/1")
        assert deleted.status_code == 200
        assert deleted.json() == {"code": 0, "message": "OK", "data": None}

        missing = client.get("/api/v1/notes/1")
        assert missing.status_code == 404
        assert missing.json() == {"code": 404, "message": "Note not found", "data": None}

        invalid = client.post("/api/v1/notes", json={"title": ""})
        assert invalid.status_code == 422
        assert invalid.json() == {"code": 422, "message": "请求参数错误", "data": None}
    finally:
        app.dependency_overrides.pop(get_note_service, None)


def test_unhandled_error_uses_response_envelope_without_leaking_details() -> None:
    class FailingNoteService(FakeNoteService):
        async def list(self, offset: int, limit: int) -> list[SimpleNamespace]:
            raise RuntimeError("private database details")

    app.dependency_overrides[get_note_service] = FailingNoteService
    try:
        response = TestClient(app, raise_server_exceptions=False).get("/api/v1/notes")
        assert response.status_code == 500
        assert response.json() == {"code": 500, "message": "服务器内部错误", "data": None}
    finally:
        app.dependency_overrides.pop(get_note_service, None)
