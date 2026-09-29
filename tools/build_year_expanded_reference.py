"""Merge the visible original-site year-card expansion captures."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "output" / "year_expanded_reference_2026_2035.json",
    ROOT / "output" / "year_expanded_reference_2031_2040.json",
)
TARGET = ROOT / "core" / "year_expanded_reference.json"
SUMMARY_SOURCE = ROOT / "output" / "year_sha_visible_2031_2040.json"
SUMMARY_TARGET = ROOT / "core" / "year_sha_reference.json"


def build() -> dict:
    merged = {}
    for path in SOURCES:
        for card in json.loads(path.read_text(encoding="utf-8")):
            year = str(card["year"])
            row = {
                "ganzhi": card["ganzhi"],
                "sha": [[item["name"], item["value"]] for item in card["sha"]],
                "good": [[item["name"], item["value"]] for item in card["good"]],
            }
            if not 40 <= len(row["sha"]) <= 45 or len(row["good"]) != 25:
                raise ValueError(f"Incomplete expanded year card: {year}")
            if any(not name or not value for group in ("sha", "good") for name, value in row[group]):
                raise ValueError(f"Empty expanded year field: {year}")
            if year in merged and merged[year] != row:
                raise ValueError(f"Conflicting original-site captures: {year}")
            merged[year] = row
    TARGET.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summaries = json.loads(SUMMARY_TARGET.read_text(encoding="utf-8"))
    for card in json.loads(SUMMARY_SOURCE.read_text(encoding="utf-8"))["cards"]:
        year = str(card["year"])
        if year in summaries and summaries[year] != card["rows"]:
            raise ValueError(f"Conflicting original-site year summary: {year}")
        summaries[year] = card["rows"]
    SUMMARY_TARGET.write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    return merged


if __name__ == "__main__":
    result = build()
    print(f"Saved {len(result)} verified year expansions to {TARGET}")
