from __future__ import annotations
from typing import List, Set, Iterator, Any, Optional, Sequence, Generator
import os
import re
from pathlib import Path
# from clang.cindex import Index, Cursor, CursorKind, TypeKind, Config, TranslationUnit, FileInclusion, AccessSpecifier
from jinja2 import Environment, FileSystemLoader
import yaml

dir_codegen: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'codegen'
dir_data : Path = dir_codegen / 'data' 

file_loader = FileSystemLoader(dir_codegen / 'templates')

env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

template_lean = env.get_template('lean/class.lean.j2')
template_cpp = env.get_template('cpp/class.cpp.j2')

with open(dir_data / 'mock.yml', 'rt') as f:
    mock_data = yaml.safe_load(f.read())

output = template_lean.render(**mock_data)

print(output)

output = template_cpp.render(**mock_data)

print(output)

