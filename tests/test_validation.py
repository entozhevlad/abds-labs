import unittest

from pydantic import TypeAdapter, ValidationError

from app.api.types import DateString, UInt32
from app.api.update_user.schemas import UpdateUserRequest
from app.system.time import timestamp


class ValidationTests(unittest.TestCase):
    def test_unsigned_integer_bounds(self) -> None:
        for value in (-1, True, 1.5, "1", None, 2**32):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                TypeAdapter(UInt32).validate_python(value)
        self.assertEqual(TypeAdapter(UInt32).validate_python(0), 0)
        self.assertEqual(TypeAdapter(UInt32).validate_python(2**32 - 1), 2**32 - 1)

    def test_strict_dates(self) -> None:
        for value in (
            None,
            "",
            "2026-2-01",
            "2026-02-29",
            "2026-10-01 12:00:00",
            "1800-01-01",
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                TypeAdapter(DateString).validate_python(value)
        self.assertEqual(
            TypeAdapter(DateString).validate_python("2024-02-29"), "2024-02-29"
        )

    def test_patch_requires_nonempty_nonnull_fields(self) -> None:
        for value in (
            {},
            {"fio": None},
            {"phone": None},
            {"fio": "  "},
            {"fio": 123},
            {"other": "x"},
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                UpdateUserRequest.model_validate(value)
        self.assertEqual(
            UpdateUserRequest(phone="123").model_dump(exclude_unset=True),
            {"phone": "123"},
        )

    def test_version_increases_with_second_precision(self) -> None:
        self.assertEqual(timestamp("2099-01-01 00:00:00"), "2099-01-01 00:00:01")
