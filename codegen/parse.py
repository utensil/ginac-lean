from __future__ import annotations
from typing import List, Set, Iterator, Any, Optional, Sequence, Generator
import os
import re
from pathlib import Path
from clang.cindex import Index, Cursor, CursorKind, TypeKind, Config, TranslationUnit, FileInclusion, AccessSpecifier

index: Index = Index.create()

build: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'build'
ginac: str = 'ginac-1.8.7/ginac'

ginac_header: Path = build / ginac / 'ginac.h'

index_args: List[str] = ['-xc++', '-std=c++11']

ginac_ast: TranslationUnit = index.parse(ginac_header, args=index_args)

class MethodCollector:
    recursive: bool = True
    visited_headers: Set[str] = set()

    def __init__(self, recursive):
        self.recursive = recursive

    def should_skip(self, file_name: str) -> bool:
        return file_name in self.visited_headers

    def walk(self, ast: TranslationUnit) -> Iterator[Cursor]:
        if self.recursive:
            for include in ast.get_includes():
                included_filename : str = include.include.name
                included_ast: TranslationUnit = index.parse(included_filename, args=index_args)
                if not self.should_skip(included_filename):
                    self.visited_headers.add(included_filename)
                    for cursor in self.walk(included_ast):
                        yield cursor
        
        for cursor in ast.cursor.walk_preorder():
            yield cursor

concerned_cursor_kinds : List[CursorKind] = [
    CursorKind.STRUCT_DECL,
    CursorKind.TYPEDEF_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CONSTRUCTOR,
    CursorKind.DESTRUCTOR,
    CursorKind.CXX_METHOD,
    CursorKind.CLASS_TEMPLATE
]

collector = MethodCollector(recursive=True)

PATH_ROOT_REGEX = re.compile('.*/ginac-lean/build/ginac-1.8.7/')

for cursor in collector.walk(ginac_ast):
    if cursor.kind in concerned_cursor_kinds:
        if cursor.access_specifier == AccessSpecifier.PUBLIC:
            print(
                PATH_ROOT_REGEX.sub('', cursor.translation_unit.spelling),
                cursor.kind,
                cursor.type.spelling,
                f"`{cursor.lexical_parent.spelling}::{cursor.spelling}`",
                f"`{cursor.semantic_parent.spelling}::{cursor.spelling}`"
                # , cursor.mangled_name) segmentation fault
            )
            if cursor.kind in [CursorKind.CONSTRUCTOR, CursorKind.CXX_METHOD]:
                for arg_type in cursor.type.argument_types():
                    pointee_type = arg_type.get_pointee()
                    print(
                        f'\t{arg_type.spelling}',
                        'pod' if arg_type.is_pod() else '',
                        'const_qualified' if arg_type.is_const_qualified() else '',
                        pointee_type.spelling,
                        'pointee_pod' if pointee_type.is_pod() else '',
                        'pointee_const_qualified' if pointee_type.is_const_qualified() else '',
                    )