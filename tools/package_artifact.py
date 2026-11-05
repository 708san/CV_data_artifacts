"""共通形式のartifactをタイムスタンプ固定のZIPへまとめる。"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def package(source_root: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    files = sorted(path for path in source_root.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in source_root.rglob("*")):
        raise ValueError("symlink is not allowed in an artifact")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    package(args.source_root, args.destination)
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
