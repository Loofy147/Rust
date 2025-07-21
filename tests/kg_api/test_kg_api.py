import pytest
from httpx import AsyncClient
from kg_api.main import app

@pytest.mark.asyncio
async def test_add_and_get_entity():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login to get JWT
        resp = await ac.post("/token", data={"username": "admin", "password": "adminpass"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Add entity
        entity = {"type": "CONCEPT", "name": "Test Entity", "properties": {"foo": "bar"}}
        resp = await ac.post("/entities", json=entity, headers=headers)
        assert resp.status_code == 200
        eid = resp.json()["id"]
        # Get entity
        resp = await ac.get(f"/entities/{eid}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Entity"

@pytest.mark.asyncio
async def test_add_and_get_relationship():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login to get JWT
        resp = await ac.post("/token", data={"username": "admin", "password": "adminpass"})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Add two entities
        e1 = await ac.post("/entities", json={"type": "CONCEPT", "name": "A"}, headers=headers)
        e2 = await ac.post("/entities", json={"type": "CONCEPT", "name": "B"}, headers=headers)
        id1 = e1.json()["id"]
        id2 = e2.json()["id"]
        # Add relationship
        rel = {"source_id": id1, "target_id": id2, "type": "DEPENDS_ON"}
        resp = await ac.post("/relationships", json=rel, headers=headers)
        assert resp.status_code == 200
        rid = resp.json()["id"]
        # Get relationship
        resp = await ac.get(f"/relationships/{rid}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == id1 and data["target_id"] == id2