#!/usr/bin/env python3
"""Detect repeated non-trivial code blocks in Python files.

This complements detect_duplicate_functions.py by finding duplicated line
windows that do not necessarily form complete functions.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import fnmatch
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


IGNORE_DIRS = {
    ".git", ".qwen", ".venv", ".venv-1", ".vscode",
    "build", "build_gen", "dist", "dist_gen", "installer_output",
    "logs", "__pycache__",
}


@dataclass(frozen=True)
class BlockHit:
    path: Path
    start_line: int
    end_line: int
    preview: str


def iter_python_files(root: Path, include: list[str], exclude: list[str]) -> list[Path]:
    files: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [
            name for name in dir_names
            if name not in IGNORE_DIRS and not name.startswith(".venv")
        ]
        for file_name in file_names:
            path = Path(current_root) / file_name
            if path.suffix.lower() == ".py":
                rel = str(path.relative_to(root)).replace("\\", "/")
                if include and not any(fnmatch.fnmatch(rel, pattern) for pattern in include):
                    continue
                if exclude and any(fnmatch.fnmatch(rel, pattern) for pattern in exclude):
                    continue
                files.append(path)
    return files


def normalized_lines(path: Path, ignore_strings: bool) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    in_triple_string = False
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            triple_count = stripped.count('"""') + stripped.count("'''")
            if ignore_strings and triple_count:
                if triple_count % 2 == 1:
                    in_triple_string = not in_triple_string
                continue
            if ignore_strings and in_triple_string:
                continue
            if not stripped or stripped.startswith("#"):
                continue
            if stripped in {")", "]", "}", "(", "[", "{"}:
                continue
            result.append((line_no, " ".join(stripped.split())))
    return result


def find_duplicate_blocks(
    root: Path,
    window: int,
    min_chars: int,
    include: list[str],
    exclude: list[str],
    same_file_only: bool,
    ignore_strings: bool,
) -> dict[str, list[BlockHit]]:
    groups: dict[str, list[BlockHit]] = defaultdict(list)
    for path in iter_python_files(root, include, exclude):
        lines = normalized_lines(path, ignore_strings)
        if len(lines) < window:
            continue
        for index in range(0, len(lines) - window + 1):
            chunk = lines[index:index + window]
            block_text = "\n".join(line for _line_no, line in chunk)
            if len(block_text) < min_chars:
                continue
            digest = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
            groups[digest].append(BlockHit(
                path=path,
                start_line=chunk[0][0],
                end_line=chunk[-1][0],
                preview=chunk[0][1][:100],
            ))
    duplicates: dict[str, list[BlockHit]] = {}
    for digest, hits in groups.items():
        if len(hits) <= 1:
            continue
        if same_file_only and len({hit.path for hit in hits}) > 1:
            continue
        duplicates[digest] = hits
    return duplicates


def remove_overlapping_groups(groups: list[list[BlockHit]]) -> list[list[BlockHit]]:
    selected: list[list[BlockHit]] = []
    occupied: set[tuple[Path, int]] = set()
    for hits in groups:
        hit_lines = {
            (hit.path, line_no)
            for hit in hits
            for line_no in range(hit.start_line, hit.end_line + 1)
        }
        if hit_lines & occupied:
            continue
        selected.append(hits)
        occupied.update(hit_lines)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect repeated code blocks by normalized line windows.")
    parser.add_argument("root", nargs="?", default=".", help="Project root directory")
    parser.add_argument("--window", type=int, default=8, help="Number of normalized lines per block")
    parser.add_argument("--min-chars", type=int, default=120, help="Minimum normalized block size")
    parser.add_argument("--limit", type=int, default=30, help="Maximum duplicate groups to print")
    parser.add_argument("--include", action="append", default=[], help="Glob path to include, relative to root. Can be repeated")
    parser.add_argument("--exclude", action="append", default=[], help="Glob path to exclude, relative to root. Can be repeated")
    parser.add_argument("--same-file-only", action="store_true", help="Only report duplicates that occur within one file")
    parser.add_argument("--ignore-strings", action="store_true", help="Ignore triple-quoted string blocks such as stylesheets/templates")
    parser.add_argument("--keep-overlaps", action="store_true", help="Keep overlapping duplicate windows in the report")
    args = parser.parse_args()

    duplicates = find_duplicate_blocks(
        Path(args.root).resolve(),
        args.window,
        args.min_chars,
        args.include,
        args.exclude,
        args.same_file_only,
        args.ignore_strings,
    )
    if not duplicates:
        print("No duplicated code blocks found.")
        return

    sorted_groups = sorted(
        duplicates.values(),
        key=lambda hits: (len(hits), hits[0].end_line - hits[0].start_line),
        reverse=True,
    )
    if not args.keep_overlaps:
        sorted_groups = remove_overlapping_groups(sorted_groups)
    print(f"Found {len(sorted_groups)} duplicated code block groups:\n")
    for group_index, hits in enumerate(sorted_groups[:args.limit], start=1):
        print(f"Group {group_index}: {len(hits)} matches")
        for hit in hits:
            print(f"  - {hit.path}:{hit.start_line}-{hit.end_line}  {hit.preview}")
        print()


if __name__ == "__main__":
    main()
