import os
from pathlib import Path
from clang.cindex import Index, CursorKind, TypeKind, Config, TranslationUnit

index = Index.create()

build = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'build'
ginac = 'ginac-1.8.7/ginac'

ginac = build / ginac / 'add.h'

index_args = ['-xc++', '-std=c++11']

ginac_ast = index.parse(ginac, args=index_args)

def walk(ast, recursive=True):
    if recursive:
        for include in ast.get_includes():
            included_ast = index.parse(include.include.name, args=index_args)
            for cursor in walk(included_ast):
                yield cursor
        
    for cursor in ast.cursor.walk_preorder():
        yield cursor

concerned_cursor_kinds = [
    CursorKind.STRUCT_DECL,
    CursorKind.TYPEDEF_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CONSTRUCTOR,
    CursorKind.DESTRUCTOR,
    CursorKind.CXX_METHOD,
    CursorKind.CLASS_TEMPLATE
]

for cursor in walk(ginac_ast, False):
    if cursor.kind in concerned_cursor_kinds:
        print(cursor.translation_unit.spelling, cursor.kind, cursor.type.spelling, f"`{cursor.lexical_parent.spelling}::{cursor.spelling}`") # , cursor.mangled_name) segmentation fault
