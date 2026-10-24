"""Private, atomic JSON profiles under SKILL_DATA_DIR (Linux/macOS standard library)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA_VERSION = 1
HOME_DATA_SUBDIR = Path(".local/share/cubbie-knowledge-dna")


class StoreError(ValueError):
    def __init__(self, message: str, code="profile_error"):
        super().__init__(message)
        self.code = code


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def new_profile(learner_id):
    return {"schema_version": SCHEMA_VERSION, "learner_id": learner_id, "revision": 0,
            "created_at": utc_now(), "updated_at": None, "concepts": {},
            "observations": [], "interventions": [], "session": None, "session_history": []}


def summarize(profile):
    """A bounded view for Cubbie's first-8,000-character tool result window."""
    concepts = profile["concepts"]
    session = profile.get("session")
    scope = session["scope"] if session else []
    demonstrated = [c for c in scope if concepts.get(c, {}).get("status") == "demonstrated"]
    untested = [c for c in scope if concepts.get(c, {}).get("status") == "untested"]
    uncertain = [c for c in scope if concepts.get(c, {}).get("status") in {"uncertain", "suspected"}]
    # Unparseable observations are evidence of uncertainty, never incorrect math.
    if session and session["state"] == "uncertain":
        uncertain = list(dict.fromkeys(uncertain + ([session["focus"]] if session.get("focus") else [])))
    recent = profile["interventions"][-3:]
    unresolved = [c for c in scope if c not in demonstrated]
    recommendations = unresolved[:3]
    last_transfer = recent[-1].get("transfer") if recent else None
    if last_transfer and last_transfer["verdict"] == "incorrect":
        recommendations = list(dict.fromkeys([recent[-1]["concept"] + ":attention_application"] + recommendations))[:3]
    if not recommendations and session:
        recommendations = ["spaced_review", "multi_head_attention"] if session["target"] == "transformer_attention" else ["transformer_attention"]
    return {
        "concepts_tested": list(dict.fromkeys(o["concept"] for o in profile["observations"])),
        "questions_answered": len(profile["observations"]),
        "scored_answers": sum(o["verdict"] != "unscored" for o in profile["observations"]),
        "demonstrated_understanding": demonstrated,
        "demonstration_scope": "Limited practice items, not durable mastery or proof of every prerequisite.",
        "uncertain_knowledge_gaps": uncertain, "untested_concepts": untested,
        "misconception_patterns_detected": list(dict.fromkeys(
            o["misconception"] for o in profile["observations"] if o["misconception"])),
        "lessons_delivered": sum(i["lesson_delivered"] for i in profile["interventions"]),
        "improvements_verified": sum(i["outcome"] == "improvement_verified" for i in profile["interventions"]),
        "recent_interventions": [{k: i[k] for k in ("concept", "outcome", "reassessment", "transfer")}
                                 for i in recent],
        "recommended_next_concepts": recommendations,
        "sessions_recorded": len(profile["session_history"]) + bool(session),
    }


class ProfileStore:
    def __init__(self, root=None):
        self.configuration = "explicit" if root is not None else "skill_data_dir"
        root = root if root is not None else os.environ.get("SKILL_DATA_DIR")
        if not root:
            home = os.environ.get("HOME")
            if not home or not Path(home).is_absolute():
                raise StoreError(
                    "Provide an absolute SKILL_DATA_DIR or persistent HOME; no profile was saved.",
                    "missing_data_dir",
                )
            # The guide guarantees student HOME persists even if the Skill folder changes.
            root = str(Path(home) / HOME_DATA_SUBDIR)
            os.environ["SKILL_DATA_DIR"] = root
            self.configuration = "persistent_home"
        self.root = Path(root).expanduser()
        if not self.root.is_absolute():
            raise StoreError("SKILL_DATA_DIR must be an absolute path", "invalid_data_dir")
        self.directory = self.root / "profiles"
        if self.directory.is_symlink():
            raise StoreError("The profiles directory must not be a symlink")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def storage_info(self):
        return {"data_dir": str(self.root), "configuration": self.configuration}

    def check(self):
        """Exercise writing, atomic replacement and reading without changing learning history."""
        with tempfile.TemporaryDirectory(prefix=".storage-check-", dir=self.root) as directory:
            pending = Path(directory) / "probe.tmp"
            committed = Path(directory) / "probe.json"
            marker = {"storage_check": True}
            with pending.open("w", encoding="utf-8") as handle:
                json.dump(marker, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(pending, committed)
            if json.loads(committed.read_text(encoding="utf-8")) != marker:
                raise StoreError("Storage read-back did not match the write", "storage_unavailable")
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return {"ok": True, "storage": dict(self.storage_info(), read_write_verified=True)}

    def path(self, learner):
        if not isinstance(learner, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", learner):
            raise StoreError("Use an opaque learner ID: 1-64 letters, digits, underscores or hyphens", "invalid_learner_id")
        return self.directory / f"{learner}.json"

    @contextmanager
    def locked(self, learner):
        path = self.path(learner).with_suffix(".lock")
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def validate(self, profile, learner):
        if not isinstance(profile, dict) or profile.get("schema_version") != SCHEMA_VERSION:
            raise StoreError("Unsupported or missing profile schema; preserve the file.", "unsupported_schema")
        required = {"learner_id": str, "revision": int, "concepts": dict,
                    "observations": list, "interventions": list, "session_history": list}
        if any(type(profile.get(k)) is not t for k, t in required.items()):
            raise StoreError("Malformed profile; preserve the file.", "corrupt_profile")
        if profile["learner_id"] != learner or profile["revision"] < 0:
            raise StoreError("Profile identity or revision is invalid", "corrupt_profile")
        statuses = {"untested", "suspected", "uncertain", "likely_gap", "demonstrated", "needs_practice"}
        for record in profile["concepts"].values():
            if (not isinstance(record, dict) or record.get("status") not in statuses
                    or not isinstance(record.get("evidence_question_ids"), list)):
                raise StoreError("Invalid concept record", "corrupt_profile")
        for observation in profile["observations"]:
            if (not isinstance(observation, dict)
                    or any(k not in observation for k in ("question_id", "concept", "role", "answer", "misconception"))
                    or observation.get("verdict") not in {"correct", "incorrect", "unscored"}):
                raise StoreError("Invalid observation", "corrupt_profile")
        for intervention in profile["interventions"]:
            if not isinstance(intervention, dict) or any(k not in intervention for k in
                    ("concept", "outcome", "lesson_delivered", "reassessment", "transfer")):
                raise StoreError("Invalid intervention", "corrupt_profile")
        for session in profile["session_history"] + ([profile["session"]] if profile.get("session") else []):
            if (not isinstance(session, dict) or any(k not in session for k in
                    ("id", "target", "state", "scope", "evidence", "focus", "canvas", "next"))
                    or not isinstance(session["evidence"], list)
                    or not isinstance(session["scope"], list)
                    or not isinstance(session["next"], dict)
                    or any(type(i) is not int or i < 0 or i >= len(profile["observations"])
                           for i in session["evidence"])):
                raise StoreError("Invalid session", "corrupt_profile")

    def _load(self, learner):
        path = self.path(learner)
        if path.is_symlink():
            raise StoreError("Profile file must not be a symlink")
        if not path.exists():
            return new_profile(learner)
        try:
            profile = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise StoreError("Unreadable profile JSON; preserve the file.", "corrupt_profile") from exc
        self.validate(profile, learner)
        return profile

    def load(self, learner):
        with self.locked(learner):
            return self._load(learner)

    def update(self, learner, transform):
        """Serialize read/modify/write; a failed transition leaves the original file intact."""
        with self.locked(learner):
            profile = self._load(learner)
            original_revision = profile["revision"]
            profile = transform(profile)
            profile["revision"] = original_revision + 1
            profile["updated_at"] = utc_now()
            self.validate(profile, learner)
            path = self.path(learner)
            descriptor, temporary = tempfile.mkstemp(prefix=f".{learner}-", suffix=".tmp", dir=self.directory)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump(profile, handle, ensure_ascii=True, allow_nan=False, indent=2)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
                directory_fd = os.open(self.directory, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["summary", "check"])
    parser.add_argument("--learner", default="student")
    args = parser.parse_args()
    try:
        store = ProfileStore()
        if args.action == "check":
            print(json.dumps(store.check()))
        else:
            print(json.dumps({"ok": True, "storage": store.storage_info(),
                              "summary": summarize(store.load(args.learner))}))
    except (StoreError, OSError) as exc:
        print(json.dumps({"ok": False, "error": {"code": getattr(exc, "code", "io_error"), "message": str(exc)}}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
