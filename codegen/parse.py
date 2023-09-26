from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import (Any, Dict, Generator, Iterator, List, Optional, Sequence,
                    Set)

import yaml
from clang.cindex import (AccessSpecifier, Config, Cursor, CursorKind,
                          FileInclusion, Index, TranslationUnit, TypeKind,
                          conf)


def get_cxx_include_paths():
    # run `clang -v -E -x c++ - -v < /dev/null 2>&1` to get the include paths
    result = subprocess.run(['clang', '-v', '-E', '-x', 'c++', '-', '-v'], input=b'', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stderr.decode(sys.getdefaultencoding())
    search_list = output.split('#include <...> search starts here:\n')[1].split('End of search list.')[0]
    include_paths = []
    for line in search_list.split('\n'):
        line = line.strip()
        if line != '':
            include_paths.append(line)
    return include_paths

cxx_include_paths = get_cxx_include_paths()
print(f'C++ include paths: {cxx_include_paths}')

index: Index = Index.create()

dir_build: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'build'
dir_codegen: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'codegen'
dir_data : Path = dir_codegen / 'data' 

ginac: str = 'ginac-1.8.7/ginac'

ginac_header: Path = dir_build / ginac / 'symbol.h'

index_args: List[str] = ['-xc++', '-std=c++11']

# Add C++ include paths to the index or libclang fail to recognize std::string etc.
index_args.extend(['-I' + include_path for include_path in cxx_include_paths])

# print(index_args)

print(f'Parsing {ginac_header}...')
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

    def in_cxx_include_paths(self, file_name: str) -> bool:
        # TODO: the whole parsing should be embeded in this class
        # FIXME: cxx_include_paths refering to global variable
        for include_path in cxx_include_paths:
            if include_path in file_name:
                return True
        return False

    def should_skip(self, file_name: str) -> bool:
        # print(f'Checking if {file_name} should be skipped...')

        return file_name in self.visited_headers or self.in_cxx_include_paths(file_name)
    
    def visit_file(self, included_filename : str):
        # print(f'Visiting {included_filename}...')
        self.visited_headers.add(included_filename)

    def walk(self, ast: TranslationUnit) -> Iterator[Cursor]:
        if self.recursive:
            for include in ast.get_includes():
                included_filename : str = include.include.name
                if not self.should_skip(included_filename):
                    self.visit_file(included_filename)
                    # FIXME: index_args referring to global variable
                    included_ast: TranslationUnit = index.parse(included_filename, args=index_args)
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

def check_valid(cursor: Cursor):
    pass
    # if cursor.kind.is_invalid():
    #     print(f'\tINVALID!!! {cursor.spelling}')

# If libclang can't determine a type, it's int! Should be fixed by adding C++ include paths to the index.
# Here we have a hacky way to detect this error.
# TODO: find a better way to detect argument type parsing error
def check_arg_valid(cursor: Cursor):
    check_valid(cursor)
    token_spellings = ' '.join([token.spelling for token in cursor.get_tokens()])
    # If the argument type is int, but the token spellings don't contain 'int', it's probably a parsing error
    # Can confirm this works by removing C++ include paths from the index, then parse symbol.h which refers to std::string,
    # it will print out a lot of warnings like:
    # WARN Invalid argument type detected: const int & != const std :: string & initname at ginac-lean/build/ginac-1.8.7/ginac/symbol.h:43:38
    if 'int' in cursor.type.spelling and 'int' not in token_spellings:
        if 'unsigned int' in cursor.type.spelling:
            # Exclude false positives like:
            # WARN Invalid argument type detected: unsigned int != unsigned inf at ginac-lean/build/ginac-1.8.7/ginac/symbol.h:48:21
            return
        # TODO: gather all the warnings and print them at the end, then give hints on how to fix them
        print(f'WARN Invalid argument type detected: {cursor.type.spelling} != {token_spellings} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}', file=sys.stderr)

for cursor in collector.walk(ginac_ast):
    if cursor.kind in concerned_cursor_kinds:
        check_valid(cursor)
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
                    check_arg_valid(arg)
                    referenced = arg.referenced
                    # check_arg_valid(referenced)
                    print(
                        f'\t{referenced.spelling}',
                        referenced.type.spelling,
                        arg.get_usr(),
                        arg.get_num_template_arguments()
                        )
                    arg_type = arg.type
                    if arg.kind.is_invalid():
                        print(f'\tINVALID!!! {arg_type.spelling}')
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