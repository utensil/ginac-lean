from __future__ import annotations

import os
import re
import unittest
from pathlib import Path
from typing import Any, Generator, Iterator, List, Optional, Sequence, Set

import pytest
import yaml

# from clang.cindex import Index, Cursor, CursorKind, TypeKind, Config, TranslationUnit, FileInclusion, AccessSpecifier
from jinja2 import Environment, FileSystemLoader

dir_root: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent.parent
dir_build: Path = dir_root / "build"
dir_codegen: Path = dir_root / "codegen"
dir_fixture: Path = dir_codegen / "tests" / "fixtures"

UPDATE_FIXTURES = False


# TODO: extract the the implemetation out of tests
class TestGenerate(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_generate_lean(self):
        file_loader = FileSystemLoader(dir_codegen / "templates")
        env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        template_lean = env.get_template("lean/class.lean.j2")

        mock_data = yaml.safe_load(
            (dir_fixture / "mock.yml").read_text(encoding="utf-8")
        )

        expected_lean = (dir_fixture / "mock.lean").read_text(encoding="utf-8")

        actual_lean = template_lean.render(**mock_data)

        if UPDATE_FIXTURES:
            (dir_fixture / "mock.lean").write_text(actual_lean, encoding="utf-8")

        self.assertMultiLineEqual(actual_lean, expected_lean)

    def test_generate_cpp(self):
        file_loader = FileSystemLoader(dir_codegen / "templates")
        env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        template_cpp = env.get_template("cpp/class.cpp.j2")

        mock_data = yaml.safe_load(
            (dir_fixture / "mock.yml").read_text(encoding="utf-8")
        )

        expected_cpp = (dir_fixture / "mock.cpp").read_text(encoding="utf-8")

        actual_cpp = template_cpp.render(**mock_data)

        if UPDATE_FIXTURES:
            (dir_fixture / "mock.cpp").write_text(actual_cpp, encoding="utf-8")

        self.assertMultiLineEqual(actual_cpp, expected_cpp)
