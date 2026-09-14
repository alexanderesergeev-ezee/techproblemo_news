import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize(text: str) -> str:
    return " ".join(text.split())


@dataclass(frozen=True)
class RunResult:
    read: int = 0
    new: int = 0
    duplicates: int = 0
    classified: int = 0
    queued: int = 0
    sent: int = 0
    failed: int = 0
    needs_review: int = 0
    skipped_no_text: int = 0


MIGRATION = """
CREATE TABLE IF NOT EXISTS runtime_state (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, type TEXT NOT NULL, locator TEXT NOT NULL, enabled INTEGER NOT NULL,
 approval_state TEXT NOT NULL, permission_ref TEXT NOT NULL, next_fetch_at TEXT,
 cursor_json TEXT, last_success_at TEXT, last_error TEXT
);
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), source_item_id TEXT NOT NULL,
 source_url TEXT, published_at TEXT, observed_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 raw_text TEXT NOT NULL, content_hash TEXT NOT NULL, process_status TEXT NOT NULL,
 next_attempt_at TEXT, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
 UNIQUE(source_id, source_item_id)
);
CREATE TABLE IF NOT EXISTS analyses (
 id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id), content_hash TEXT NOT NULL,
 provider TEXT NOT NULL, model TEXT NOT NULL, prompt_version TEXT NOT NULL,
 validated_json TEXT NOT NULL, created_at TEXT NOT NULL, usage_json TEXT NOT NULL,
 UNIQUE(message_id, content_hash, provider, model, prompt_version)
);
CREATE TABLE IF NOT EXISTS deliveries (
 id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
 analysis_id INTEGER NOT NULL REFERENCES analyses(id), target_chat_id TEXT NOT NULL,
 payload TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 started_at TEXT, next_attempt_at TEXT, sent_at TEXT, telegram_message_id TEXT, last_error TEXT,
 UNIQUE(message_id, target_chat_id)
);
CREATE INDEX IF NOT EXISTS messages_queue ON messages(process_status, next_attempt_at);
CREATE INDEX IF NOT EXISTS deliveries_queue ON deliveries(status, next_attempt_at);
INSERT OR IGNORE INTO runtime_state(key, value_json) VALUES ('schema_version', '1');
"""


class Pipeline:
    def __init__(self, database: Path, schema: Path, output: Path, threshold: float = 0.70):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.executescript(MIGRATION)
        self.schema = json.loads(schema.read_text(encoding="utf-8"))
        self.output = output
        self.threshold = threshold

    def close(self) -> None:
        self.connection.close()

    def run(self, fixture: Path) -> RunResult:
        cases = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line]
        counts = {field: 0 for field in RunResult.__dataclass_fields__}
        counts["read"] = len(cases)
        for case in cases:
            self._ensure_source(case)
            text = normalize(case.get("text", ""))
            digest = hashlib.sha256(text.encode()).hexdigest()
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO messages(source_id,source_item_id,source_url,published_at,"
                "observed_at,updated_at,raw_text,content_hash,process_status) VALUES(?,?,?,?,?,?,?,?,?)",
                (case["source_id"], case["source_item_id"], case.get("source_url"),
                 case.get("published_at"), utc_now(), utc_now(), text, digest,
                 "NEW" if text else "SKIPPED_NO_TEXT"),
            )
            self.connection.commit()
            if not cursor.rowcount:
                counts["duplicates"] += 1
                continue
            counts["new"] += 1
            if not text:
                counts["skipped_no_text"] += 1
                continue
            outcome = self._classify(cursor.lastrowid, digest, text, case.get("mock_classification"))
            counts[outcome] += 1
        counts["sent"] = self._deliver()
        return RunResult(**counts)

    def _ensure_source(self, case: dict) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO sources(id,type,locator,enabled,approval_state,permission_ref) "
            "VALUES(?, 'fixture', 'local-jsonl', 1, 'approved', 'synthetic')",
            (case["source_id"],),
        )

    def _classify(self, message_id: int, digest: str, text: str, response: object) -> str:
        error = None
        for attempt in range(1, 4):
            error = self._validation_error(response, text)
            if error is None:
                break
        if error:
            self.connection.execute(
                "UPDATE messages SET process_status='FAILED',attempts=?,last_error=? WHERE id=?",
                (attempt, error, message_id),
            )
            self.connection.commit()
            return "failed"
        assert isinstance(response, dict)
        status = "NEEDS_REVIEW" if response["insufficient_context"] else "CLASSIFIED"
        eligible = (
            response["relevance_score"] > self.threshold
            and not response["insufficient_context"]
            and response["category"] != "not_relevant"
        )
        with self.connection:
            analysis = self.connection.execute(
                "INSERT INTO analyses(message_id,content_hash,provider,model,prompt_version,"
                "validated_json,created_at,usage_json) VALUES(?,?,?,?,?,?,?,?)",
                (message_id, digest, "mock", "fixture", "classify_v1",
                 json.dumps(response, ensure_ascii=False), utc_now(), "{}"),
            )
            self.connection.execute(
                "UPDATE messages SET process_status=?,attempts=?,last_error=NULL WHERE id=?",
                (status, attempt, message_id),
            )
            if eligible:
                payload = self._card(message_id, response)
                self.connection.execute(
                    "INSERT INTO deliveries(message_id,analysis_id,target_chat_id,payload,status) "
                    "VALUES(?,?,? ,?,'PENDING')",
                    (message_id, analysis.lastrowid, "offline-file", payload),
                )
        return "queued" if eligible else ("needs_review" if status == "NEEDS_REVIEW" else "classified")

    def _validation_error(self, response: object, text: str) -> str | None:
        if not isinstance(response, dict):
            return "invalid classifier response: object required"
        required = set(self.schema["required"])
        if set(response) != required:
            return "invalid classifier response: missing or additional fields"
        properties = self.schema["properties"]
        score = response["relevance_score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
            return "invalid classifier response: relevance_score must be between 0 and 1"
        if response["category"] not in properties["category"]["enum"]:
            return "invalid classifier response: unknown category"
        if not isinstance(response["insufficient_context"], bool):
            return "invalid classifier response: insufficient_context must be boolean"
        if not all(isinstance(response[name], str) for name in ("summary_ru", "reason_ru")):
            return "invalid classifier response: summary and reason must be strings"
        if not isinstance(response["evidence"], list) or not all(
            isinstance(item, str) for item in response["evidence"]
        ):
            return "invalid classifier response: evidence must be an array of strings"
        missing = [evidence for evidence in response["evidence"] if evidence not in text]
        return "evidence is absent from source text" if missing else None

    def _card(self, message_id: int, response: dict) -> str:
        return (f"{response['summary_ru']}\nКатегория: {response['category']}\n"
                f"Оценка: {response['relevance_score']:.2f}\nПричина: {response['reason_ru']}\n"
                f"Внутренний ID: {message_id}")

    def _deliver(self) -> int:
        rows = self.connection.execute(
            "SELECT id,payload FROM deliveries WHERE status='PENDING' ORDER BY id"
        ).fetchall()
        if not rows:
            return 0
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8") as stream:
            for row in rows:
                with self.connection:
                    self.connection.execute(
                        "UPDATE deliveries SET status='SENDING',started_at=?,attempts=attempts+1 "
                        "WHERE id=? AND status='PENDING'",
                        (utc_now(), row["id"]),
                    )
                stream.write(json.dumps({"delivery_id": row["id"], "payload": row["payload"]},
                                        ensure_ascii=False) + "\n")
                stream.flush()
                with self.connection:
                    self.connection.execute(
                        "UPDATE deliveries SET status='SENT',sent_at=? WHERE id=?",
                        (utc_now(), row["id"]),
                    )
        return len(rows)
