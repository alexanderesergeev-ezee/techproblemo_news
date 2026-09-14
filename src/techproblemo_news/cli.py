import argparse
import json
from pathlib import Path

from .pipeline import Pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run-once")
    run.add_argument("--offline", action="store_true", required=True)
    run.add_argument("--database", type=Path, default=Path("data/offline.sqlite3"))
    run.add_argument("--input", type=Path, default=Path("evals/synthetic_cases.jsonl"))
    run.add_argument("--output", type=Path, default=Path("data/deliveries.jsonl"))
    args = parser.parse_args(argv)
    pipeline = Pipeline(args.database, Path("schemas/classification.schema.json"), args.output)
    try:
        print(json.dumps(pipeline.run(args.input).__dict__, ensure_ascii=False, sort_keys=True))
    finally:
        pipeline.close()
    return 0
