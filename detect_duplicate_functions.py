#!/usr/bin/env python3
"""Detect deeper duplicate Python functions across the workspace.

This script parses Python source files, normalizes function bodies by
canonicalizing local identifiers, and groups functions that have the same
structural AST. It helps find repeated logic even when variable names differ.
"""

import argparse
import ast
import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

IGNORE_DIRS = {"build", "build_gen", "dist", "installer_output", ".venv", "logs", "__pycache__"}
PYTHON_EXTENSIONS = {".py"}

BUILTIN_NAMES = set(dir(__builtins__))
BUILTIN_NAMES.update({"self", "cls"})


@dataclass
class FunctionInfo:
    file_path: Path
    line: int
    qualified_name: str
    ast_hash: str
    body_dump: str


class Normalizer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.name_map: Dict[str, str] = {}
        self.counter = 0

    def _normalize_name(self, name: str) -> str:
        if name in BUILTIN_NAMES:
            return name
        if name not in self.name_map:
            self.name_map[name] = f"v{self.counter}"
            self.counter += 1
        return self.name_map[name]

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._normalize_name(node.arg)
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
            node.id = self._normalize_name(node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = "func"
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node.name = "func"
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        node.name = "Class"
        return self.generic_visit(node)


def iter_source_files(root: Path, extensions: Set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in IGNORE_DIRS:
                continue
        elif path.suffix.lower() in extensions:
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            yield path


def get_function_nodes(tree: ast.AST, file_path: Path) -> Iterable[Tuple[str, ast.AST, int]]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = getattr(node, "parent", None)
            parent_names = []
            while parent is not None:
                if isinstance(parent, ast.ClassDef):
                    parent_names.append(parent.name)
                parent = getattr(parent, "parent", None)
            parent_names.reverse()
            qualname = "".join(f"{name}." for name in parent_names)
            qualname += node.name
            yield qualname, node, node.lineno


def attach_parents(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            setattr(child, "parent", node)


def normalize_function(node: ast.AST) -> Tuple[str, str]:
    normalizer = Normalizer()
    node_copy = ast.fix_missing_locations(node)
    normalized = normalizer.visit(node_copy)
    ast.fix_missing_locations(normalized)
    dump = ast.dump(normalized, include_attributes=False)
    digest = hashlib.sha256(dump.encode("utf-8")).hexdigest()
    return digest, dump


def parse_file(path: Path) -> List[FunctionInfo]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    attach_parents(tree)
    functions: List[FunctionInfo] = []
    for qualname, node, lineno in get_function_nodes(tree, path):
        digest, dump = normalize_function(node)
        functions.append(FunctionInfo(path, lineno, qualname, digest, dump))
    return functions


def find_duplicates(root: Path, min_matches: int = 2) -> Dict[str, List[FunctionInfo]]:
    groups: Dict[str, List[FunctionInfo]] = defaultdict(list)
    for path in iter_source_files(root, PYTHON_EXTENSIONS):
        for function in parse_file(path):
            groups[function.ast_hash].append(function)
    return {h: fns for h, fns in groups.items() if len(fns) >= min_matches}


def print_report(duplicates: Dict[str, List[FunctionInfo]]) -> None:
    if not duplicates:
        print("No duplicated function bodies found.")
        return
    print(f"Found {len(duplicates)} duplicated function groups:\n")
    for index, (digest, functions) in enumerate(sorted(duplicates.items(), key=lambda item: len(item[1]), reverse=True), 1):
        print(f"Group {index}: {len(functions)} matches")
        for fn in functions:
            print(f"  - {fn.file_path}:{fn.line}  ({fn.qualified_name})")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect duplicate Python functions by normalizing AST structure.")
    parser.add_argument("root", nargs="?", default=".", help="Project root directory to scan")
    parser.add_argument("--min-matches", type=int, default=2, help="Minimum number of duplicates to report")
    parser.add_argument("--extensions", default=".py", help="Comma-separated file extensions to scan")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    extensions = {ext.strip().lower() if ext.startswith('.') else f".{ext.strip().lower()}" for ext in args.extensions.split(",")}

    duplicates = find_duplicates(root, min_matches=args.min_matches)
    print_report(duplicates)


if __name__ == "__main__":
    main()
