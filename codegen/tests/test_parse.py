from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Sequence, Set

import pytest
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

dir_root: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent.parent
dir_build: Path = dir_root / "build"
dir_codegen: Path = dir_root / "codegen"
dir_fixture: Path = dir_codegen / "tests" / "fixtures"

ginac: str = "ginac-1.8.7/ginac"

concerned_cursor_kinds: List[CursorKind] = [
    CursorKind.STRUCT_DECL,
    CursorKind.TYPEDEF_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CONSTRUCTOR,
    CursorKind.DESTRUCTOR,
    CursorKind.CXX_METHOD,
    CursorKind.CLASS_TEMPLATE,
]

PATH_ROOT_REGEX = re.compile(".*/ginac-lean/build/ginac-1.8.7/")

UPDATE_FIXTURES = "UPDATE_FIXTURES" in os.environ


class TestParse(unittest.TestCase):
    def setUp(self) -> None:
        self.collector = EntityCollector(recursive=True)
        print(f"C++ include paths: {self.collector.cpp_include_paths}")

    # regenerate with
    # UPDATE_FIXTURES=1 pytest codegen/tests -k ginac_all -s --no-skip
    # FIXME: less nested blocks
    # pylint: disable=too-many-nested-blocks
    @pytest.mark.skip(reason="only test locally for now")
    # @pytest.mark.skipif("CI" not in os.environ, reason="Only run on CI")
    def test_parse_ginac_all(self):
        ginac_header: Path = dir_build / ginac / "ginac.h"
        print(f"Parsing {ginac_header}...")
        ginac_ast: TranslationUnit = self.collector.parse(ginac_header)

        with open(dir_fixture / "all_methods.txt", "w", encoding="utf-8") as file:
            collector = self.collector
            for cursor in collector.walk(ginac_ast):
                if cursor.kind in concerned_cursor_kinds:
                    check_valid(cursor)
                    if cursor.access_specifier == AccessSpecifier.PUBLIC:
                        print(
                            PATH_ROOT_REGEX.sub("", cursor.translation_unit.spelling),
                            cursor.kind,
                            cursor.type.spelling,
                            f"`{cursor.lexical_parent.spelling}::{cursor.spelling}`",
                            f"`{cursor.semantic_parent.spelling}::{cursor.spelling}`",
                            # , cursor.mangled_name) segmentation fault,
                            file=file,
                        )
                        if cursor.brief_comment:
                            print(
                                "\tDOC: ", cursor.brief_comment, file=file
                            )  # raw_comment

                        if cursor.kind in [
                            CursorKind.CONSTRUCTOR,
                            CursorKind.CXX_METHOD,
                        ]:
                            for arg in cursor.get_arguments():
                                check_arg_valid(arg, file=file)
                                referenced = arg.referenced
                                # check_arg_valid(referenced)
                                print(
                                    f"\t{referenced.spelling}",
                                    referenced.type.spelling,
                                    arg.get_usr(),
                                    arg.get_num_template_arguments(),
                                    file=file,
                                )
                                arg_type = arg.type
                                if arg.kind.is_invalid():
                                    print(
                                        f"\tINVALID!!! {arg_type.spelling}", file=file
                                    )
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
                                    "const_qualified"
                                    if arg_type.is_const_qualified()
                                    else "",
                                    pointee_type.spelling,
                                    "pointee_pod" if pointee_type.is_pod() else "",
                                    "pointee_const_qualified"
                                    if pointee_type.is_const_qualified()
                                    else "",
                                    "......",
                                    [token.spelling for token in arg.get_tokens()],
                                    file=file,
                                )

    # see output with
    # pytest codegen/tests -k parse_symbol -s
    def test_parse_symbol(self):
        test_target = "symbol"

        ginac_header: Path = dir_build / ginac / "symbol.h"
        print(f"Parsing {ginac_header}...")
        ginac_ast: TranslationUnit = self.collector.parse(ginac_header)

        collector = self.collector
        for cursor in collector.walk(ginac_ast):
            if cursor.kind in concerned_cursor_kinds:
                check_valid(cursor)
                if (
                    cursor.access_specifier == AccessSpecifier.PUBLIC
                    and cursor.lexical_parent.spelling == test_target
                ):
                    if cursor.kind in [CursorKind.CONSTRUCTOR, CursorKind.CXX_METHOD]:
                        class_type_name = cursor.lexical_parent.spelling
                        class_cursor = cursor.lexical_parent
                        class_type = collector.find_or_create_type(
                            class_type_name, cursor.lexical_parent.type
                        )

                        return_type = (
                            ReturnType(
                                cpp=class_type_name,
                                lean=to_lean_type_name(
                                    class_type_name, class_cursor.type
                                ),
                                to_lean=to_lean_function(
                                    class_type_name, class_cursor.type
                                ),
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
                                    from_lean=from_lean_function(
                                        arg.type.spelling, arg
                                    ),
                                ),
                            )
                            for arg in cursor.get_arguments()
                        ]
                        class_type.methods.append(method)

        for class_name, class_interface in collector.data.items():
            if class_name == to_lean_type_name(test_target):
                class_interface.namespace = "Ginac"
                target_fixture = dir_fixture / f"{class_name}.yml"

                actual = yaml.dump(class_interface.to_dict())
                expected = target_fixture.read_text()

                if UPDATE_FIXTURES:
                    (dir_fixture / f"{class_name}.yml").write_text(actual)

                self.assertMultiLineEqual(actual, expected)

    def test_libclang(self):
        print(conf.lib)
