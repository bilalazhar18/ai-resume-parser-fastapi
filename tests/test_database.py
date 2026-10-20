import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.crud import users as crud
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.models.user import User
from app.security import verify_password
from app.session import get_db
from main import app
from migrate import upgrade_database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(self.engine.dispose)
        upgrade_database(self.engine)

        def override_get_db():
            with Session(self.engine) as session:
                yield session

        original_overrides = app.dependency_overrides.copy()
        self.addCleanup(
            lambda: (app.dependency_overrides.clear(), app.dependency_overrides.update(original_overrides))
        )
        app.dependency_overrides[get_db] = override_get_db

    def test_user_persists_and_response_omits_credentials(self):
        with Session(self.engine) as session:
            user = User(name="Ali", email="ali@example.com", hash_password="test-hash")
            session.add(user)
            session.commit()
            user_id = user.id

        with Session(self.engine) as session:
            user = session.get(User, user_id)
            self.assertEqual(
                UserResponse.model_validate(user).model_dump(),
                {"id": user_id, "name": "Ali", "email": "ali@example.com"},
            )

    def test_duplicate_email_is_rejected(self):
        with Session(self.engine) as session:
            session.add(User(name="Ali", email="ali@example.com", hash_password="test-hash"))
            session.commit()
            session.add(User(name="Other", email="ali@example.com", hash_password="other-hash"))
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()

    def test_crud_rolls_back_duplicate_writes(self):
        with Session(self.engine) as session:
            first = crud.create_user(session, UserCreate(name="Ali", email="ali@example.com", password="first"))
            second = crud.create_user(session, UserCreate(name="Sara", email="sara@example.com", password="second"))
            with self.assertRaises(crud.DuplicateEmailError):
                crud.create_user(session, UserCreate(name="Other", email="ali@example.com", password="other"))
            with self.assertRaises(crud.DuplicateEmailError):
                crud.user_update(session, second.id, UserUpdate(name="Changed", email="ali@example.com"))
            self.assertEqual(crud.get_user(session, second.id).email, "sara@example.com")
            self.assertEqual(crud.get_user(session, second.id).name, "Sara")
            self.assertEqual(crud.get_user(session, first.id).name, "Ali")

    def test_startup_and_existing_user_routes(self):
        with TestClient(app) as client:
            self.assertIn("users", inspect(self.engine).get_table_names())
            self.assertEqual(client.get("/").status_code, 200)
            payload = {"name": "Ali", "email": "ali@example.com", "password": "test-password"}
            created = client.post("/users", json=payload)
            self.assertEqual(created.status_code, 201)
            user_id = created.json()["id"]
            self.assertEqual(client.get(f"/users/{user_id}").json(), created.json())
            payload.update(name="Ali Updated", email="updated@example.com", password="new-password")
            updated = client.put(f"/users/{user_id}", json=payload)
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json(), {"id": user_id, "name": payload["name"], "email": payload["email"]})
            self.assertEqual(client.get(f"/users/{user_id}").json(), updated.json())
            with Session(self.engine) as session:
                stored = session.get(User, user_id).hash_password
                self.assertNotEqual(stored, "new-password")
                self.assertTrue(verify_password("new-password", stored))
            self.assertEqual(client.delete(f"/users/{user_id}").status_code, 200)
            self.assertEqual(client.get(f"/users/{user_id}").status_code, 404)
            self.assertEqual(client.put(f"/users/{user_id}", json=payload).status_code, 404)
            self.assertEqual(client.delete(f"/users/{user_id}").status_code, 404)

    def test_create_user_route_and_duplicate_email(self):
        with TestClient(app) as client:
            payload = {"name": "Ali", "email": "ali@example.com", "password": "test-password"}
            response = client.post("/users", json=payload)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(
                response.json(),
                {"id": 1, "name": "Ali", "email": "ali@example.com"},
            )
            self.assertEqual(client.post("/users", json=payload).status_code, 409)
        with Session(self.engine) as session:
            stored = session.get(User, 1).hash_password
            self.assertNotEqual(stored, payload["password"])
            self.assertTrue(verify_password(payload["password"], stored))
            self.assertFalse(verify_password("wrong-password", stored))

    def test_update_requires_json_body_and_preserves_other_users(self):
        with TestClient(app) as client:
            first = {"name": "Ali", "email": "ali@example.com", "password": "first"}
            second = {"name": "Sara", "email": "sara@example.com", "password": "second"}
            first_id = client.post("/users", json=first).json()["id"]
            second_response = client.post("/users", json=second).json()
            path = f"/users/{first_id}"
            self.assertEqual(client.put(path, params=first).status_code, 422)
            self.assertEqual(client.put(path, json={"name": "New"}).status_code, 422)
            self.assertEqual(client.put(path, json={**first, "email": second["email"]}).status_code, 409)
            self.assertEqual(client.put(path, json={**first, "name": "Updated"}).status_code, 200)
            self.assertEqual(client.get(f"/users/{second_response['id']}").json(), second_response)
            operation = client.get("/openapi.json").json()["paths"]["/users/{user_id}"]["put"]
            self.assertIn("application/json", operation["requestBody"]["content"])
            self.assertEqual([parameter["name"] for parameter in operation["parameters"]], ["user_id"])

    def test_update_without_password_preserves_existing_hash(self):
        with TestClient(app) as client:
            payload = {"name": "Ali", "email": "ali@example.com", "password": "original-password"}
            user_id = client.post("/users", json=payload).json()["id"]
            with Session(self.engine) as session:
                original_hash = session.get(User, user_id).hash_password
            for password_fields in ({}, {"password": None}):
                response = client.put(
                    f"/users/{user_id}",
                    json={"name": "Updated", "email": "updated@example.com", **password_fields},
                )
                self.assertEqual(response.status_code, 200)
                with Session(self.engine) as session:
                    self.assertEqual(session.get(User, user_id).hash_password, original_hash)
            self.assertEqual(client.put(f"/users/{user_id}", json={
                "name": "Updated", "email": "updated@example.com", "password": "",
            }).status_code, 422)
            for response in (
                client.get("/users"), client.get(f"/users/{user_id}"), client.delete(f"/users/{user_id}"),
            ):
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("hash_password", response.text)
                self.assertNotIn("original-password", response.text)


if __name__ == "__main__":
    unittest.main()
