from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from scripts.profile_store import ProfileStore, StoreError, summarize


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ProfileStore(self.directory.name)

    def test_empty_history_does_not_create_fake_progress(self):
        profile = self.store.load("new_student")
        self.assertEqual(profile["revision"], 0)
        self.assertEqual(profile["observations"], [])
        self.assertEqual(summarize(profile)["questions_answered"], 0)
        self.assertFalse(self.store.path("new_student").exists())

    def test_update_persists_and_increments_revision(self):
        first = self.store.update("student", lambda p: p)
        second = ProfileStore(self.directory.name).update("student", lambda p: p)
        self.assertEqual(second["revision"], 2)
        self.assertEqual(first["created_at"], second["created_at"])
        self.assertIsNotNone(second["updated_at"])
        self.assertEqual(self.store.load("student"), second)
        self.assertEqual(stat.S_IMODE(self.store.path("student").stat().st_mode), 0o600)
        self.assertEqual(list(self.store.directory.glob("*.tmp")), [])

    def test_independent_learners(self):
        self.store.update("one", lambda p: p)
        self.assertEqual(self.store.load("two")["revision"], 0)

    def test_failed_transition_preserves_bytes(self):
        self.store.update("student", lambda p: p)
        before = self.store.path("student").read_bytes()

        def fail(profile):
            profile["revision"] = 99
            raise ValueError("interrupted")

        with self.assertRaises(ValueError):
            self.store.update("student", fail)
        self.assertEqual(before, self.store.path("student").read_bytes())

    def test_replace_failure_preserves_original_and_cleans_temporary(self):
        self.store.update("student", lambda p: p)
        before = self.store.path("student").read_bytes()
        with patch("scripts.profile_store.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.store.update("student", lambda p: p)
        self.assertEqual(before, self.store.path("student").read_bytes())
        self.assertEqual(list(self.store.directory.glob("*.tmp")), [])

    def test_corrupt_json_is_not_reset(self):
        path = self.store.path("student")
        path.write_text("{broken")
        with self.assertRaises(StoreError) as caught:
            self.store.update("student", lambda p: p)
        self.assertEqual(caught.exception.code, "corrupt_profile")
        self.assertEqual(path.read_text(), "{broken")

    def test_future_schema_is_not_overwritten(self):
        path = self.store.path("student")
        path.write_text(json.dumps({"schema_version": 999}))
        before = path.read_bytes()
        with self.assertRaises(StoreError) as caught:
            self.store.update("student", lambda p: p)
        self.assertEqual(caught.exception.code, "unsupported_schema")
        self.assertEqual(path.read_bytes(), before)

    def test_bad_profile_shape_is_rejected(self):
        profile = self.store.load("student")
        profile["observations"] = ["invalid"]
        self.store.path("student").write_text(json.dumps(profile))
        with self.assertRaises(StoreError) as caught:
            self.store.load("student")
        self.assertEqual(caught.exception.code, "corrupt_profile")

    def test_path_traversal_and_personal_identifier_rejected(self):
        for learner in ("../outside", "/tmp/outside", "person@example.com", "", "a" * 65, None):
            with self.subTest(learner=learner), self.assertRaises(StoreError):
                self.store.load(learner)

    def test_missing_both_persistent_locations_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(StoreError) as caught:
                ProfileStore()
        self.assertEqual(caught.exception.code, "missing_data_dir")
        with self.assertRaises(StoreError):
            ProfileStore("relative-directory")

    def test_missing_skill_directory_initializes_persistent_home(self):
        with patch.dict(os.environ, {"HOME": self.directory.name}, clear=True):
            store = ProfileStore()
            expected = Path(self.directory.name) / ".local/share/cubbie-knowledge-dna"
            self.assertEqual(store.root, expected)
            self.assertEqual(os.environ["SKILL_DATA_DIR"], str(expected))
            self.assertEqual(store.configuration, "persistent_home")
            store.update("student", lambda p: p)
        with patch.dict(os.environ, {"HOME": self.directory.name}, clear=True):
            self.assertEqual(ProfileStore().load("student")["revision"], 1)

    def test_host_directory_is_preferred_to_home(self):
        with patch.dict(os.environ, {"HOME": "/unused", "SKILL_DATA_DIR": self.directory.name}, clear=True):
            store = ProfileStore()
            self.assertEqual(store.root, Path(self.directory.name))
            self.assertEqual(store.configuration, "skill_data_dir")

    def test_invalid_host_directory_does_not_change_storage_location(self):
        with patch.dict(os.environ, {"HOME": self.directory.name, "SKILL_DATA_DIR": "relative"}, clear=True):
            with self.assertRaises(StoreError) as caught:
                ProfileStore()
            self.assertEqual(caught.exception.code, "invalid_data_dir")
            self.assertFalse((Path(self.directory.name) / ".local").exists())

    def test_storage_check_verifies_io_without_changing_history(self):
        self.store.update("student", lambda p: p)
        before = self.store.path("student").read_bytes()
        result = self.store.check()
        self.assertTrue(result["storage"]["read_write_verified"])
        self.assertEqual(result["storage"]["data_dir"], self.directory.name)
        self.assertEqual(before, self.store.path("student").read_bytes())
        self.assertEqual(list(Path(self.directory.name).glob(".storage-check-*")), [])

    def test_failed_storage_check_is_reported_and_leaves_history_intact(self):
        self.store.update("student", lambda p: p)
        before = self.store.path("student").read_bytes()
        with patch("scripts.profile_store.os.replace", side_effect=OSError("read-only filesystem")):
            with self.assertRaises(OSError):
                self.store.check()
        self.assertEqual(before, self.store.path("student").read_bytes())

    def test_symlink_profile_is_rejected(self):
        other = Path(self.directory.name) / "outside.json"
        other.write_text("secret")
        self.store.path("student").symlink_to(other)
        with self.assertRaises(StoreError):
            self.store.load("student")
        self.assertEqual(other.read_text(), "secret")

    def test_parallel_updates_do_not_lose_changes(self):
        def increment(_):
            def change(profile):
                profile["counter"] = profile.get("counter", 0) + 1
                return profile
            ProfileStore(self.directory.name).update("student", change)

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(increment, range(32)))
        profile = self.store.load("student")
        self.assertEqual(profile["revision"], 32)
        self.assertEqual(profile["counter"], 32)


if __name__ == "__main__":
    unittest.main()
