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
                          FileInclusion, Index, TranslationUnit, TypeKind, Type as CppType,
                          conf)


def get_cpp_include_paths():
    # run `clang -v -E -x c++ - -v < /dev/null 2>&1` to get the include paths
    result = subprocess.run(['clang', '-v', '-E', '-x', 'c++', '-', '-v'], input=b'', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stderr.decode(sys.getdefaultencoding())
    search_list = output.split('#include <...> search starts here:\n')[-1].split('End of search list.')[0]
    include_paths = []
    for line in search_list.split('\n'):
        line = line.strip()
        if line != '':
            include_paths.append(line)
    return include_paths

cpp_include_paths = get_cpp_include_paths()
print(f'C++ include paths: {cpp_include_paths}')

index: Index = Index.create()

dir_build: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'build'
dir_codegen: Path = Path(os.path.dirname(os.path.realpath(__file__))).parent / 'codegen'
dir_data : Path = dir_codegen / 'data' 

ginac: str = 'ginac-1.8.7/ginac'

ginac_header: Path = dir_build / ginac / 'symbol.h'

index_args: List[str] = ['-xc++', '-std=c++11']

# Add C++ include paths to the index or libclang fail to recognize std::string etc.
index_args.extend(['-I' + include_path for include_path in cpp_include_paths])

# print(index_args)

print(f'Parsing {ginac_header}...')
ginac_ast: TranslationUnit = index.parse(ginac_header, args=index_args)

@dataclass
class ParamType:
    lean: str
    cpp: str
    from_lean: str

@dataclass
class ReturnType:
    lean: str
    cpp: str
    to_lean: str

@dataclass
class MethodParam:
    name: str
    type: ParamType

@dataclass
class Method:
    kind: str
    lean: str
    cpp: str
    params: List[MethodParam]
    return_type: ReturnType

@dataclass
class ClassType:
    lean: str
    cpp: str
    methods: List[Method]

@dataclass
class ClassInterface:
    namespace: str
    deps: List[Dict[str, str]]
    type: ClassType

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
                'return_type': {
                    'lean': method.return_type.lean,
                    'cpp': method.return_type.cpp,
                    'to_lean': method.return_type.to_lean
                }
            }

            for param in method.params:
                param_dict = {
                    'name': param.name,
                    'type': {
                        'lean': param.type.lean,
                        'cpp': param.type.cpp,
                        'from_lean': param.type.from_lean
                    }
                }
                method_dict['params'].append(param_dict)

            data_dict['type']['methods'].append(method_dict)

        return data_dict
    
def map_primitive_type(s, cpp_type: CppType) -> str:
    return f'LEAN_PRIMITIVE_{cpp_type.spelling}'
    
def to_lean_type_name(s, cpp_type: CppType):
    if is_primitive_type(cpp_type.kind):
        return map_primitive_type(s, cpp_type)
    if '::' in s:
        return to_lean_type_name(s.split('::')[-1], cpp_type)
    return ''.join(word.capitalize() for word in s.split('_'))

class EntityCollector:
    recursive: bool = True
    visited_headers: Set[str] = set()
    data: Dict[str, ClassInterface] = {}

    def __init__(self, recursive):
        self.recursive = recursive

    def in_cpp_include_paths(self, file_name: str) -> bool:
        # TODO: the whole parsing should be embeded in this class
        # FIXME: cpp_include_paths refering to global variable
        for include_path in cpp_include_paths:
            if include_path in file_name:
                return True
        return False

    def should_skip(self, file_name: str) -> bool:
        # print(f'Checking if {file_name} should be skipped...')

        return file_name in self.visited_headers or self.in_cpp_include_paths(file_name)
    
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

    def find_or_create_class_interface(self, type_name_cpp: str, cpp_type: CppType) -> ClassInterface:
        # Caution! It's registered in its lean name
        type_name_lean = to_lean_type_name(type_name_cpp, cpp_type)

        if type_name_lean in self.data:
            return self.data[type_name_lean]
        else:
            class_interface = ClassInterface(type_name_cpp, [],
                                             ClassType(type_name_lean, type_name_cpp, []))
            self.data[type_name_lean] = class_interface
            return class_interface

    def find_or_create_type(self, type_name_cpp: str, cpp_type: CppType) -> ClassType:
        class_interface = self.find_or_create_class_interface(type_name_cpp, cpp_type)
        return class_interface.type

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
        TypeKind.LONGDOUBLE
    ]

# FIXME maybe all these primitive types are not meant to mapped to Lean built-in types
MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE: Dict[TypeKind, str] = {
    TypeKind.BOOL: 'Bool',
    # TypeKind.CHAR_U: 'UInt8',
    # TypeKind.UCHAR: 'UInt8',
    # TypeKind.CHAR16: 'UInt16',
    # TypeKind.CHAR32: 'UInt32',
    TypeKind.USHORT: 'UInt16',
    TypeKind.UINT: 'UInt32',
    TypeKind.ULONG: 'UInt64',
    TypeKind.ULONGLONG: 'UInt64', 
    TypeKind.UINT128: 'UInt128',
    # TypeKind.CHAR_S: 'Int8',
    # TypeKind.SCHAR: 'Int8',
    # TypeKind.WCHAR: 'UInt32',
    TypeKind.SHORT: 'Int16',
    TypeKind.INT: 'Int32',
    TypeKind.LONG: 'Int64',
    TypeKind.LONGLONG: 'Int64',
    TypeKind.INT128: 'Int128',
    TypeKind.FLOAT: 'Float',
    TypeKind.DOUBLE: 'Float',
    TypeKind.LONGDOUBLE: 'Float'
}

def map_primitive_type(type_name: str, cpp_type: CppType):
    if cpp_type.kind in MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE:
        return MAP_PRIMITIVE_TYPE_TO_LEAN_TYPE[cpp_type.kind]
    else:
        return f'LEAN_PRIMITIVE_{type_name}'

def to_lean_method_name(method_name_cpp: str, cursor: Cursor) -> str:
    if cursor.kind == CursorKind.CONSTRUCTOR:
        return 'mk'
    # TODO: should keep or change getters/setters?
    else:
        return method_name_cpp
    
def from_lean_function(param_type_cpp: str, cursor: Cursor) -> str:
    if param_type_cpp in ['const std::string &', 'const char *']:
        return 'lean_string_cstr(%s)'
    else:
        print(f'WARN Unknown from_lean_function for {param_type_cpp} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}', file=sys.stderr)
        return 'UNKOWN_FROM_LEAN_FUNCTION'
    
def to_lean_function(param_type_cpp: str, cpp_type: CppType) -> str:
    if param_type_cpp in ['const std::string &']:
        return 'lean_mk_string(%s.c_str())'
    elif param_type_cpp in ['const char *']:
        return 'lean_mk_string(%s)'
    else:
        # print(f'WARN Unknown to_lean_function for {param_type_cpp} at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}', file=sys.stderr)
        print(f'INFO Default to_lean_function to as is for {param_type_cpp}') # at {cursor.location.file.name}:{cursor.location.line}:{cursor.location.column}')
        return '%s'
    
def cursor_kind_spelling(kind: CursorKind) -> str:
    if kind == CursorKind.CONSTRUCTOR:
        return 'CONSTRUCTOR'
    elif kind == CursorKind.CXX_METHOD:
        return 'CXX_METHOD'
    else:
        print(f'WARN Unknown cursor_kind_spelling for {kind}', file=sys.stderr)
        return 'UNKNOWN_CURSOR_KIND'

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
                class_type_name = cursor.lexical_parent.spelling
                class_cursor = cursor.lexical_parent
                class_type = collector.find_or_create_type(class_type_name, cursor.lexical_parent.type)

                return_type= ReturnType(
                        cpp=class_type_name,
                        lean=to_lean_type_name(class_type_name, class_cursor.type),
                        to_lean=to_lean_function(class_type_name, class_cursor.type)
                    ) if cursor.kind == CursorKind.CONSTRUCTOR else ReturnType(
                        cpp=cursor.result_type.spelling,
                        lean=to_lean_type_name(cursor.result_type.spelling, cursor.result_type),
                        to_lean=to_lean_function(cursor.result_type.spelling, cursor.result_type)
                    )

                method = Method(
                    kind=cursor_kind_spelling(cursor.kind),
                    cpp=cursor.spelling,
                    lean=to_lean_method_name(cursor.spelling, cursor),
                    params=[],
                    return_type=return_type
                )

                def to_lean_param_name(arg: Cursor) -> str:
                    if arg.type.is_pod() and is_primitive_type(arg.type.kind):
                        return map_primitive_type(arg.type.spelling, arg.type)
                    elif arg.type.spelling == 'const std::string &':
                        return '@&String'
                    else:
                        print(f'WARN Unknown to_lean_param_name for {arg.type.spelling} at {arg.location.file.name}:{arg.location.line}:{arg.location.column}', file=sys.stderr)
                        return 'UNKOWN_LEAN_PARAM_NAME'

                method.params = [MethodParam(
                    name=arg.spelling,
                    type=ParamType(
                        cpp=arg.type.spelling,
                        lean=to_lean_param_name(arg),
                        from_lean=from_lean_function(arg.type.spelling, arg)
                    )
                ) for arg in cursor.get_arguments()]
                class_type.methods.append(method)

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
    if class_name == 'Symbol':
        class_interface.namespace = 'Ginac'
        with open(dir_data / f'{class_name}.yml', 'w') as file:
            yaml.dump(class_interface.to_dict(), file)

print(conf.lib)