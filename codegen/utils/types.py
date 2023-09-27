from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Sequence, Set

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


def to_lean_type_name(type_name_cpp, cpp_type: CppType):
    if is_primitive_type(cpp_type.kind):
        return map_primitive_type(type_name_cpp, cpp_type)
    if "::" in type_name_cpp:
        return to_lean_type_name(type_name_cpp.split("::")[-1], cpp_type)
    return "".join(word.capitalize() for word in type_name_cpp.split("_"))


def check_valid(_cursor: Cursor):
    pass
    # if cursor.kind.is_invalid():
    #     print(f'\tINVALID!!! {cursor.spelling}')


# If libclang can't determine a type, it's int! Should be fixed by adding C++ include paths to the index.
# Here we have a hacky way to detect this error.
# TODO: find a better way to detect argument type parsing error
def check_arg_valid(cursor: Cursor):
    check_valid(cursor)
    token_spellings = " ".join([token.spelling for token in cursor.get_tokens()])
    # If the argument type is int, but the token spellings don't contain 'int', it's probably a parsing error
    # Can confirm this works by removing C++ include paths from the index, then parse symbol.h which refers to std::string,
    # it will print out a lot of warnings like:
    # WARN Invalid argument type detected: const int & != const std :: string & initname at ginac-lean/build/ginac-1.8.7/ginac/symbol.h:43:38
    if "int" in cursor.type.spelling and "int" not in token_spellings:
        if "unsigned int" in cursor.type.spelling:
            # Exclude false positives like:
            # WARN Invalid argument type detected: unsigned int != unsigned inf at ginac-lean/build/ginac-1.8.7/ginac/symbol.h:48:21
            return
        # TODO: gather all the warnings and print them at the end, then give hints on how to fix them
        print(
            f"WARN Invalid argument type detected: {cursor.type.spelling} != {token_spellings} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}",
            file=sys.stderr,
        )


# TODO: add more primitive types
def is_primitive_type(typekind: TypeKind):
    return typekind in [
        TypeKind.BOOL,
        # TypeKind.CHAR_U,
        # TypeKind.UCHAR,
        # TypeKind.CHAR16,
        # TypeKind.CHAR32,
        TypeKind.USHORT,
        TypeKind.UINT,
        TypeKind.ULONG,
        TypeKind.ULONGLONG,
        TypeKind.UINT128,
        # TypeKind.CHAR_S,
        # TypeKind.SCHAR,
        # TypeKind.WCHAR,
        TypeKind.SHORT,
        TypeKind.INT,
        TypeKind.LONG,
        TypeKind.LONGLONG,
        TypeKind.INT128,
        TypeKind.FLOAT,
        TypeKind.DOUBLE,
        TypeKind.LONGDOUBLE,
    ]


# FIXME maybe all these primitive types are not meant to mapped to Lean built-in types
MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE: Dict[TypeKind, str] = {
    TypeKind.BOOL: "Bool",
    # TypeKind.CHAR_U: 'UInt8',
    # TypeKind.UCHAR: 'UInt8',
    # TypeKind.CHAR16: 'UInt16',
    # TypeKind.CHAR32: 'UInt32',
    TypeKind.USHORT: "UInt16",
    TypeKind.UINT: "UInt32",
    TypeKind.ULONG: "UInt64",
    TypeKind.ULONGLONG: "UInt64",
    TypeKind.UINT128: "UInt128",
    # TypeKind.CHAR_S: 'Int8',
    # TypeKind.SCHAR: 'Int8',
    # TypeKind.WCHAR: 'UInt32',
    TypeKind.SHORT: "Int16",
    TypeKind.INT: "Int32",
    TypeKind.LONG: "Int64",
    TypeKind.LONGLONG: "Int64",
    TypeKind.INT128: "Int128",
    TypeKind.FLOAT: "Float",
    TypeKind.DOUBLE: "Float",
    TypeKind.LONGDOUBLE: "Float",
}


def map_primitive_type(type_name: str, cpp_type: CppType):
    if cpp_type.kind in MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE:
        return MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE[cpp_type.kind]
    else:
        return f"LEAN_PRIMITIVE_{type_name}"


def to_lean_method_name(method_name_cpp: str, cursor: Cursor) -> str:
    if cursor.kind == CursorKind.CONSTRUCTOR:
        return "mk"
    # TODO: should keep or change getters/setters?
    else:
        return method_name_cpp


def from_lean_function(param_type_cpp: str, cursor: Cursor) -> str:
    if param_type_cpp in ["const std::string &", "const char *"]:
        return "lean_string_cstr(%s)"
    else:
        print(
            f"WARN Unknown from_lean_function for {param_type_cpp} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}",
            file=sys.stderr,
        )
        return "UNKOWN_FROM_LEAN_FUNCTION"


def to_lean_function(param_type_cpp: str, _cpp_type: CppType) -> str:
    if param_type_cpp in ["const std::string &"]:
        return "lean_mk_string(%s.c_str())"
    elif param_type_cpp in ["const char *"]:
        return "lean_mk_string(%s)"
    else:
        # print(f'WARN Unknown to_lean_function for {param_type_cpp} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}', file=sys.stderr)
        print(
            f"INFO Default to_lean_function to as is for {param_type_cpp}"
        )  # at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}')
        return "%s"


def cursor_kind_spelling(kind: CursorKind) -> str:
    if kind == CursorKind.CONSTRUCTOR:
        return "CONSTRUCTOR"
    elif kind == CursorKind.CXX_METHOD:
        return "CXX_METHOD"
    else:
        print(f"WARN Unknown cursor_kind_spelling for {kind}", file=sys.stderr)
        return "UNKNOWN_CURSOR_KIND"


def to_lean_param_name(arg: Cursor) -> str:
    if arg.type.is_pod() and is_primitive_type(arg.type.kind):
        return map_primitive_type(arg.type.spelling, arg.type)
    elif arg.type.spelling == "const std::string &":
        return "@&String"
    else:
        print(
            f"WARN Unknown to_lean_param_name for {arg.type.spelling} at {arg.location.file.name}:{arg.location.line}:{arg.location.column}",
            file=sys.stderr,
        )
        return "UNKOWN_LEAN_PARAM_NAME"
