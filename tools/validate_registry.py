"""CV_data_artifactsの台帳を標準ライブラリだけで検証する。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "datasets.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = {
    "dataset_id", "artifact_version", "artifact_url", "artifact_sha256",
    "source_url", "source_version", "source_sha256", "license",
    "rights_status", "attribution", "modifications", "transform_version",
    "manifest_url", "audit_report_url",
}


def _https(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or urlparse(value).scheme != "https":
        errors.append(f"{field} must be an https URL")


def validate(path: Path = REGISTRY) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read registry: {exc}"]
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("repository") != "708san/CV_data_artifacts":
        errors.append("repository must be 708san/CV_data_artifacts")
    datasets = data.get("datasets")
    if not isinstance(datasets, list):
        return errors + ["datasets must be a list"]
    ids: set[str] = set()
    for index, item in enumerate(datasets):
        prefix = f"datasets[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED - set(item)
        errors.extend(f"{prefix} missing {field}" for field in sorted(missing))
        dataset_id = item.get("dataset_id")
        if not isinstance(dataset_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", dataset_id):
            errors.append(f"{prefix}.dataset_id is invalid")
        elif dataset_id in ids:
            errors.append(f"{prefix}.dataset_id is duplicated: {dataset_id}")
        else:
            ids.add(dataset_id)
        for field in ("artifact_url", "source_url", "manifest_url", "audit_report_url"):
            _https(item.get(field), f"{prefix}.{field}", errors)
        for field in ("artifact_sha256", "source_sha256"):
            if not isinstance(item.get(field), str) or not SHA256.fullmatch(item[field]):
                errors.append(f"{prefix}.{field} must be a lowercase SHA-256")
        if item.get("rights_status") != "approved_for_redistribution":
            errors.append(f"{prefix}.rights_status must allow redistribution")
        if not isinstance(item.get("modifications"), list):
            errors.append(f"{prefix}.modifications must be a list")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    print(f"registry valid: {REGISTRY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
