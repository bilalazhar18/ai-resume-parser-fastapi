import unittest

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from app.database import Base
from app.security import hash_password, verify_password
from migrate import upgrade_database


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        self.addCleanup(self.engine.dispose)

    def test_fresh_database_matches_models_and_can_upgrade_twice(self):
        upgrade_database(self.engine)
        upgrade_database(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.scalar(text("SELECT version_num FROM alembic_version")), "0002")
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])

    def test_existing_users_are_preserved_and_passwords_hashed_once(self):
        Base.metadata.create_all(self.engine)
        already_hashed = hash_password("already-secure")
        with self.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO users (id, name, email, hash_password) VALUES (:id, :name, :email, :password)"
            ), [
                {"id": 1, "name": "Ali", "email": "ali@example.com", "password": "legacy-password"},
                {"id": 2, "name": "Sara", "email": "sara@example.com", "password": already_hashed},
            ])
        upgrade_database(self.engine)
        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT id, name, email, hash_password FROM users ORDER BY id")).all()
            self.assertEqual(rows[0][:3], (1, "Ali", "ali@example.com"))
            self.assertTrue(verify_password("legacy-password", rows[0][3]))
            self.assertEqual(rows[1][3], already_hashed)
        upgrade_database(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.scalar(text("SELECT hash_password FROM users WHERE id = 1")), rows[0][3])

    def test_incompatible_legacy_schema_is_not_stamped(self):
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)"))
        with self.assertRaisesRegex(RuntimeError, "differs from the baseline"):
            upgrade_database(self.engine)
        with self.engine.connect() as connection:
            self.assertIsNone(connection.scalar(text(
                "SELECT name FROM sqlite_master WHERE name = 'alembic_version'"
            )))
