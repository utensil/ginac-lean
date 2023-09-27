from __future__ import annotations

import os
import re
import sys
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

# FIXME: properly make it a package
from utils.clang import get_cpp_include_paths
from utils.collector import EntityCollector
from utils.interface import (
    ClassInterface,
    ClassType,
    Method,
    MethodParam,
    ParamType,
    ReturnType,
)
from utils.types import (
    check_arg_valid,
    check_valid,
    cursor_kind_spelling,
    from_lean_function,
    to_lean_function,
    to_lean_method_name,
    to_lean_param_name,
    to_lean_type_name,
)

cpp_include_paths = get_cpp_include_paths()
print(f"C++ include paths: {cpp_include_paths}")

index: Index = Index.create()

dir_build: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / "build"
dir_codegen: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / "codegen"
dir_data: Path = dir_codegen / "data"

ginac: str = "ginac-1.8.7/ginac"

ginac_header: Path = dir_build / ginac / "symbol.h"

concerned_cursor_kinds: List[CursorKind] = [
    CursorKind.STRUCT_DECL,
    CursorKind.TYPEDEF_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CONSTRUCTOR,
    CursorKind.DESTRUCTOR,
    CursorKind.CXX_METHOD,
    CursorKind.CLASS_TEMPLATE,
]

collector = EntityCollector(recursive=True)

print(f"Parsing {ginac_header}...")
ginac_ast: TranslationUnit = collector.parse(ginac_header)

PATH_ROOT_REGEX = re.compile(".*/ginac-lean/build/ginac-1.8.7/")

for cursor in collector.walk(ginac_ast):
    if cursor.kind in concerned_cursor_kinds:
        check_valid(cursor)
        if (
            cursor.access_specifier == AccessSpecifier.PUBLIC
            and cursor.lexical_parent.spelling == "symbol"
        ):
            print(
                PATH_ROOT_REGEX.sub("", cursor.translation_unit.spelling),
                cursor.kind,
                cursor.type.spelling,
                f"`{cursor.lexical_parent.spelling}::{cursor.spelling}`",
                f"`{cursor.semantic_parent.spelling}::{cursor.spelling}`"
                # , cursor.mangled_name) segmentation fault
            )
            if cursor.brief_comment:
                print("\tDOC: ", cursor.brief_comment)  # raw_comment

            if cursor.kind in [CursorKind.CONSTRUCTOR, CursorKind.CXX_METHOD]:
                class_type_name = cursor.lexical_parent.spelling
                class_cursor = cursor.lexical_parent
                class_type = collector.find_or_create_type(
                    class_type_name, cursor.lexical_parent.type
                )

                return_type = (
                    ReturnType(
                        cpp=class_type_name,
                        lean=to_lean_type_name(class_type_name, class_cursor.type),
                        to_lean=to_lean_function(class_type_name, class_cursor.type),
                    )
                    if cursor.kind == CursorKind.CONSTRUCTOR
                    else ReturnType(
                        cpp=cursor.result_type.spelling,
                        lean=to_lean_type_name(
                            cursor.result_type.spelling, cursor.result_type
                        ),
                        to_lean=to_lean_function(
                            cursor.result_type.spelling, cursor.result_type
                        ),
                    )
                )

                method = Method(
                    kind=cursor_kind_spelling(cursor.kind),
                    cpp=cursor.spelling,
                    lean=to_lean_method_name(cursor.spelling, cursor),
                    params=[],
                    return_type=return_type,
                )

                method.params = [
                    MethodParam(
                        name=arg.spelling,
                        type=ParamType(
                            cpp=arg.type.spelling,
                            lean=to_lean_param_name(arg),
                            from_lean=from_lean_function(arg.type.spelling, arg),
                        ),
                    )
                    for arg in cursor.get_arguments()
                ]
                class_type.methods.append(method)

                for arg in cursor.get_arguments():
                    check_arg_valid(arg)
                    referenced = arg.referenced
                    # check_arg_valid(referenced)
                    print(
                        f"\t{referenced.spelling}",
                        referenced.type.spelling,
                        arg.get_usr(),
                        arg.get_num_template_arguments(),
                    )
                    arg_type = arg.type
                    if arg.kind.is_invalid():
                        print(f"\tINVALID!!! {arg_type.spelling}")
                    pointee_type = arg_type.get_pointee()
                    print(
                        f"\t{arg_type.spelling}",
                        arg.spelling,
                        arg.displayname,
                        arg_type.get_named_type().spelling,
                        "......",
                        pointee_type.spelling,
                        "......",
                        "pod" if arg_type.is_pod() else "",
                        "const_qualified" if arg_type.is_const_qualified() else "",
                        pointee_type.spelling,
                        "pointee_pod" if pointee_type.is_pod() else "",
                        "pointee_const_qualified"
                        if pointee_type.is_const_qualified()
                        else "",
                        "......",
                        [token.spelling for token in arg.get_tokens()],
                    )

for class_name, class_interface in collector.data.items():
    if class_name == "Symbol":
        class_interface.namespace = "Ginac"
        with open(dir_data / f"{class_name}.yml", "w", encoding="utf-8") as file:
            yaml.dump(class_interface.to_dict(), file)

print(conf.lib)
