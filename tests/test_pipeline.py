import json
import sqlite3
from pathlib import Path

from techproblemo_news.pipeline import Pipeline


ROOT = Path(__file__).parents[1]


def run_fixture(tmp_path: Path, cases: list[dict]):
    fixture = tmp_path / "cases.jsonl"
    fixture.write_text("\n".join(json.dumps(case) for case in cases), encoding="utf-8")
    database = tmp_path / "test.sqlite3"
    output = tmp_path / "deliveries.jsonl"
    pipeline = Pipeline(database, ROOT / "schemas/classification.schema.json", output)
    result = pipeline.run(fixture)
    pipeline.close()
    return result, database, output


def case(item: str, score: float = 0.71, *, insufficient: bool = False) -> dict:
    text = "Система была недоступна десять минут."
    return {
        "source_id": "fixture", "source_item_id": item, "text": text,
        "mock_classification": {
            "relevance_score": score, "category": "availability",
            "insufficient_context": insufficient, "summary_ru": "Сбой.",
            "reason_ru": "Описана недоступность.", "evidence": ["недоступна десять минут"],
        },
    }


def test_strict_threshold_and_insufficient_context(tmp_path):
    result, database, output = run_fixture(
        tmp_path, [case("boundary", 0.70), case("above", 0.71), case("short", 0.99, insufficient=True)]
    )
    assert (result.queued, result.sent, result.needs_review) == (1, 1, 1)
    assert len(output.read_text(encoding="utf-8").splitlines()) == 1
    connection = sqlite3.connect(database)
    assert connection.execute(
        "SELECT process_status FROM messages WHERE source_item_id='short'"
    ).fetchone()[0] == "NEEDS_REVIEW"


def test_repeat_is_idempotent(tmp_path):
    fixture = tmp_path / "cases.jsonl"
    fixture.write_text(json.dumps(case("same")), encoding="utf-8")
    database, output = tmp_path / "db.sqlite3", tmp_path / "sent.jsonl"
    pipeline = Pipeline(database, ROOT / "schemas/classification.schema.json", output)
    assert pipeline.run(fixture).sent == 1
    repeated = pipeline.run(fixture)
    pipeline.close()
    assert (repeated.new, repeated.duplicates, repeated.sent) == (0, 1, 0)
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT count(*) FROM analyses").fetchone()[0] == 1
    assert connection.execute("SELECT count(*) FROM deliveries").fetchone()[0] == 1


def test_invalid_classifier_response_fails_instead_of_becoming_irrelevant(tmp_path):
    invalid = case("invalid")
    invalid["mock_classification"]["relevance_score"] = 1.2
    result, database, output = run_fixture(tmp_path, [invalid])
    assert (result.failed, result.sent) == (1, 0)
    assert not output.exists()
    connection = sqlite3.connect(database)
    status, attempts = connection.execute(
        "SELECT process_status,attempts FROM messages"
    ).fetchone()
    assert (status, attempts) == ("FAILED", 3)


def test_absent_evidence_and_empty_text_are_not_delivered(tmp_path):
    invented = case("invented")
    invented["mock_classification"]["evidence"] = ["этого в тексте нет"]
    empty = case("empty")
    empty["text"] = ""
    result, database, _ = run_fixture(tmp_path, [invented, empty])
    assert (result.failed, result.skipped_no_text, result.sent) == (1, 1, 0)
    connection = sqlite3.connect(database)
    statuses = dict(connection.execute("SELECT source_item_id,process_status FROM messages"))
    assert statuses == {"invented": "FAILED", "empty": "SKIPPED_NO_TEXT"}
