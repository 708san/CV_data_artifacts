"""source file inventoryを標準ライブラリだけで検証する。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read source manifest: {exc}"]
    if data.get("manifest_type") != "source_file_inventory": errors.append("manifest_type is invalid")
    if data.get("manifest_version") != "1.0.0": errors.append("manifest_version is invalid")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", data.get("dataset_id", "")): errors.append("dataset_id is invalid")
    if urlparse(data.get("source_url", "")).scheme != "https": errors.append("source_url must be https")
    files = data.get("files")
    if not isinstance(files, list) or len(files) != data.get("file_count"):
        errors.append("file_count does not match files")
        files = files if isinstance(files, list) else []
    ids: set[str] = set(); paths: set[str] = set()
    for index, item in enumerate(files):
        prefix = f"files[{index}]"
        if not isinstance(item, dict): errors.append(f"{prefix} is not an object"); continue
        for key in ("path", "file_id", "filename", "size", "sha256", "download_url"):
            if key not in item: errors.append(f"{prefix} missing {key}")
        value=item.get("path", "")
        if not isinstance(value,str) or value.startswith("/") or "\\" in value or ".." in value.split("/") or value in paths:
            errors.append(f"{prefix}.path is invalid or duplicated")
        paths.add(value)
        file_id=item.get("file_id", "")
        if not isinstance(file_id,str) or not file_id or file_id in ids: errors.append(f"{prefix}.file_id is invalid or duplicated")
        ids.add(file_id)
        if not isinstance(item.get("size"),int) or item.get("size",-1)<0: errors.append(f"{prefix}.size is invalid")
        if not isinstance(item.get("sha256"),str) or not SHA256.fullmatch(item.get("sha256","")): errors.append(f"{prefix}.sha256 is invalid")
        if urlparse(item.get("download_url","")).scheme != "https": errors.append(f"{prefix}.download_url must be https")
    return errors


def main() -> int:
    paths = [Path(value) for value in sys.argv[1:]] or sorted(Path("manifests/sources").glob("*.json"))
    errors=[]
    for path in paths: errors.extend(f"{path}: {error}" for error in validate(path))
    if errors: sys.stderr.write("\n".join(errors)+"\n"); return 1
    print(f"source manifests valid: {len(paths)}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
