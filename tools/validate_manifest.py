"""manifest-v1を標準ライブラリだけで検証する。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = {
    "manifest_version", "dataset_id", "artifact_version", "files", "image_count",
    "label_format", "transform_version", "license", "attribution", "source",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read manifest: {exc}"]
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    errors.extend(f"missing {key}" for key in sorted(REQUIRED - set(data)))
    if data.get("manifest_version") != "1.0.0":
        errors.append("manifest_version must be 1.0.0")
    if not isinstance(data.get("dataset_id"), str) or not re.fullmatch(r"[a-z][a-z0-9_]*", data.get("dataset_id", "")):
        errors.append("dataset_id is invalid")
    if not isinstance(data.get("files"), list) or not data.get("files"):
        errors.append("files must be a non-empty list")
    seen: set[str] = set()
    for index, item in enumerate(data.get("files", [])):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("path", "sha256", "size"):
            if key not in item:
                errors.append(f"{prefix} missing {key}")
        path_text = item.get("path")
        if not isinstance(path_text, str) or not path_text or path_text.startswith("/") or "\\" in path_text or ".." in path_text.split("/"):
            errors.append(f"{prefix}.path is unsafe")
        elif path_text in seen:
            errors.append(f"{prefix}.path is duplicated: {path_text}")
        else:
            seen.add(path_text)
        if not isinstance(item.get("sha256"), str) or not SHA256.fullmatch(item.get("sha256", "")):
            errors.append(f"{prefix}.sha256 must be lowercase SHA-256")
        if not isinstance(item.get("size"), int) or item.get("size", -1) < 0:
            errors.append(f"{prefix}.size must be a non-negative integer")
    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if not isinstance(source.get("url"), str) or urlparse(source.get("url", "")).scheme != "https":
            errors.append("source.url must be https")
        if not isinstance(source.get("version"), str) or not source.get("version"):
            errors.append("source.version is required")
        if not isinstance(source.get("sha256"), str) or not SHA256.fullmatch(source.get("sha256", "")):
            errors.append("source.sha256 must be lowercase SHA-256")
    if not isinstance(data.get("image_count"), int) or data.get("image_count", -1) < 0:
        errors.append("image_count must be a non-negative integer")
    return errors


def main() -> int:
    paths = [Path(value) for value in sys.argv[1:]]
    if not paths:
        paths = sorted(
            path for path in Path("manifests").glob("*.json")
            if not path.name.endswith(".schema.json")
        )
    errors = []
    for path in paths:
        errors.extend(f"{path}: {error}" for error in validate(path))
    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    print(f"manifests valid: {len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
