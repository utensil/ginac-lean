from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Sequence, Set, Union

import yaml
from clang.cindex import (
    AccessSpecifier,
    Config,
    Cursor,
    CursorKind,
    FileInclusion,
    Index,
    TranslationUnit,
)
from clang.cindex import Type as CppType
from clang.cindex import TypeKind, conf
from utils.clang import get_cpp_include_paths
from utils.interface import (
    ClassInterface,
    ClassType,
    Method,
    MethodParam,
    ParamType,
    ReturnType,
)
from utils.types import to_lean_type_name


class EntityCollector:
    recursive: bool = True
    visited_headers: Set[str] = set()
    data: Dict[str, ClassInterface] = {}
    cpp_include_paths: List[str] = []
    index: Index = None
    index_args: List[str] = ["-xc++", "-std=c++11"]

    def __init__(self, recursive):
        self.recursive = recursive
        self.index = Index.create()
        # Add C++ include paths to the index or libclang fail to recognize std::string etc.
        self.index_args.extend(
            ["-I" + include_path for include_path in self.get_cpp_include_paths()]
        )

    def parse(self, file: Path) -> TranslationUnit:
        return self.index.parse(file, args=self.index_args)

    def get_cpp_include_paths(self):
        if not self.cpp_include_paths:
            self.cpp_include_paths = get_cpp_include_paths()

        return self.cpp_include_paths

    def in_cpp_include_paths(self, file_name: str) -> bool:
        # TODO: the whole parsing should be embeded in this class
        for include_path in self.cpp_include_paths:
            if include_path in file_name:
                return True
        return False

    def should_skip(self, file_name: str) -> bool:
        # print(f'Checking if {file_name} should be skipped...')

        return file_name in self.visited_headers or self.in_cpp_include_paths(file_name)

    def visit_file(self, included_filename: str):
        # print(f'Visiting {included_filename}...')
        self.visited_headers.add(included_filename)

    def walk(self, ast: TranslationUnit) -> Iterator[Cursor]:
        if self.recursive:
            for include in ast.get_includes():
                included_filename: str = include.include.name
                if not self.should_skip(included_filename):
                    self.visit_file(included_filename)
                    # FIXME: index_args referring to global variable
                    included_ast: TranslationUnit = self.index.parse(
                        included_filename, args=self.index_args
                    )
                    for inner_cursor in self.walk(included_ast):
                        yield inner_cursor

        for cursor in ast.cursor.walk_preorder():
            yield cursor

    def find_or_create_class_interface(
        self, type_name_cpp: str, cpp_type: CppType
    ) -> ClassInterface:
        # Caution! It's registered in its lean name
        type_name_lean = to_lean_type_name(type_name_cpp, cpp_type)

        if type_name_lean in self.data:
            return self.data[type_name_lean]

        class_interface = ClassInterface(
            type_name_cpp, [], ClassType(type_name_lean, type_name_cpp, [])
        )
        self.data[type_name_lean] = class_interface
        return class_interface

    def find_or_create_type(self, type_name_cpp: str, cpp_type: CppType) -> ClassType:
        class_interface = self.find_or_create_class_interface(type_name_cpp, cpp_type)
        return class_interface.type
