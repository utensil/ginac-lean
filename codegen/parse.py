from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import (Any, Dict, Generator, Iterator, List, Optional, Sequence, Set)

import yaml
from clang.cindex import (AccessSpecifier, Config, Cursor, CursorKind,
                          FileInclusion, Index, TranslationUnit, TypeKind, conf)

index: Index = Index.create()

dir_build: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'build'
dir_codegen: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'codegen'
dir_data : Path = dir_codegen / 'data' 

ginac: str = 'ginac-1.8.7/ginac'

ginac_header: Path = dir_build / ginac / 'symbol.h'

index_args: List[str] = ['-xc++', '-std=c++11']

ginac_ast: TranslationUnit = index.parse(ginac_header, args=index_args)

@dataclass
class MethodParam:
    name: str
    type: Dict[str, str]

@dataclass
class Method:
    kind: str
    lean: str
    cpp: str
    params: List[MethodParam]
    return_type: Dict[str, str]

@dataclass
class Type:
    lean: str
    cpp: str
    methods: List[Method]

@dataclass
class ClassInterface:
    namespace: str
    deps: List[Dict[str, str]]
    type: Type

    def to_dict(self: ClassInterface):
        data_dict = {
            'namespace': self.namespace,
            'deps': self.deps,
            'type': {
                'lean': self.type.lean,
                'cpp': self.type.cpp,
                'methods': []
            }
        }

        for method in self.type.methods:
            method_dict = {
                'kind': method.kind,
                'lean': method.lean,
                'cpp': method.cpp,
                'params': [],
                'return_type': method.return_type
            }

            for param in method.params:
                param_dict = {
                    'name': param.name,
                    'type': param.type
                }
                method_dict['params'].append(param_dict)

            data_dict['type']['methods'].append(method_dict)

        return data_dict

class EntityCollector:
    recursive: bool = True
    visited_headers: Set[str] = set()
    data: Dict[str, ClassInterface] = {}

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

collector = EntityCollector(recursive=True)

PATH_ROOT_REGEX = re.compile('.*/ginac-lean/build/ginac-1.8.7/')

for cursor in collector.walk(ginac_ast):
    if cursor.kind in concerned_cursor_kinds:
        if cursor.access_specifier == AccessSpecifier.PUBLIC and cursor.lexical_parent.spelling == 'symbol':
            print(
                PATH_ROOT_REGEX.sub('', cursor.translation_unit.spelling),
                cursor.kind,
                cursor.type.spelling,
                f"`{cursor.lexical_parent.spelling}::{cursor.spelling}`",
                f"`{cursor.semantic_parent.spelling}::{cursor.spelling}`"
                # , cursor.mangled_name) segmentation fault
            )
            if cursor.brief_comment:
                print('\tDOC: ', cursor.brief_comment) # raw_comment

            if cursor.kind in [CursorKind.CONSTRUCTOR, CursorKind.CXX_METHOD]:
                for arg in cursor.get_arguments():
                    referenced = arg.referenced
                    print(
                        f'\t{referenced.spelling}',
                        referenced.type.spelling,
                        arg.get_usr(),
                        arg.get_num_template_arguments()
                        )
                    arg_type = arg.type
                    print(f'\t{arg.type.spelling}')
                    pointee_type = arg_type.get_pointee()
                    print(
                        f'\t{arg_type.spelling}',
                        arg.spelling,
                        arg.displayname,
                        arg_type.get_named_type().spelling,
                        '......',
                        pointee_type.spelling,
                        '......',
                        'pod' if arg_type.is_pod() else '',
                        'const_qualified' if arg_type.is_const_qualified() else '',
                        pointee_type.spelling,
                        'pointee_pod' if pointee_type.is_pod() else '',
                        'pointee_const_qualified' if pointee_type.is_const_qualified() else '',
                        '......',
                        [token.spelling for token in arg.get_tokens()]
                    )

for class_name, class_interface in collector.data.items():
    if class_name == 'symbol':
        class_interface['namespace'] = 'Ginac'
        with open(dir_data / f'{class_name}.yml', 'w') as file:
            yaml.dump(class_interface.to_dict(), file)


print(conf.lib)