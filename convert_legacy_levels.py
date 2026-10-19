"""Convert legacy pickled .lvl files into versioned JSON .lvl files."""

from __future__ import annotations

import argparse
from pathlib import Path

from local.level_format import read_level_records, write_level_records


def convert_file(source: Path, destination: Path, overwrite: bool = False) -> bool:
    records, is_legacy = read_level_records(source)
    if not is_legacy:
        return False
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_level_records(records, destination)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Legacy .lvl file or directory")
    parser.add_argument(
        "destination",
        type=Path,
        help="Output .lvl file, or output directory when source is a directory",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing destination files",
    )
    args = parser.parse_args()

    if args.source.is_file():
        if args.destination.exists() and args.destination.is_dir():
            destination = args.destination / args.source.name
        else:
            destination = args.destination
        converted = convert_file(args.source, destination, args.overwrite)
        print(f"{'Converted' if converted else 'Skipped'} {args.source} -> {destination}")
        return 0

    if not args.source.is_dir():
        parser.error(f"Source does not exist: {args.source}")

    files = sorted(args.source.rglob("*.lvl"))
    converted_count = 0
    skipped_count = 0
    error_count = 0
    for source in files:
        destination = args.destination / source.relative_to(args.source)
        try:
            if convert_file(source, destination, args.overwrite):
                converted_count += 1
            else:
                skipped_count += 1
        except (OSError, ValueError) as error:
            error_count += 1
            print(f"ERROR: Could not convert {source}: {error}")
    print(
        f"Converted {converted_count} legacy levels; skipped {skipped_count} "
        f"new-format levels; failed {error_count} files."
    )
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
