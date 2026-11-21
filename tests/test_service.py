import unittest
from threading import Lock
from unittest.mock import Mock

from app.services.energosbyt import EnergosbytService


class UserUpdateTests(unittest.TestCase):
    def test_update_inserts_new_version_without_mutation(self) -> None:
        db = Mock()
        db.rows.return_value = [
            {
                "id": 1,
                "fio": "Старое имя",
                "phone": "111",
                "phone_prev": "",
                "created_at": "2026-01-01 00:00:00",
                "updated_at": "2026-01-01 00:00:00",
            }
        ]
        service = EnergosbytService(db, Lock())

        service.update_user(1, {"fio": "Новое имя", "phone": "222"})

        db.execute.assert_not_called()
        db.insert.assert_called_once()
        table, rows = db.insert.call_args.args
        self.assertEqual(table, "dim_users")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["fio"], "Новое имя")
        self.assertEqual(rows[0]["phone"], "222")
        self.assertEqual(rows[0]["phone_prev"], "111")
        self.assertEqual(rows[0]["created_at"], "2026-01-01 00:00:00")
        self.assertGreater(rows[0]["updated_at"], "2026-01-01 00:00:00")
