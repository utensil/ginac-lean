from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Sequence, Set

import yaml


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
            "namespace": self.namespace,
            "deps": self.deps,
            "type": {"lean": self.type.lean, "cpp": self.type.cpp, "methods": []},
        }

        for method in self.type.methods:
            method_dict = {
                "kind": method.kind,
                "lean": method.lean,
                "cpp": method.cpp,
                "params": [],
                "return_type": {
                    "lean": method.return_type.lean,
                    "cpp": method.return_type.cpp,
                    "to_lean": method.return_type.to_lean,
                },
            }

            for param in method.params:
                param_dict = {
                    "name": param.name,
                    "type": {
                        "lean": param.type.lean,
                        "cpp": param.type.cpp,
                        "from_lean": param.type.from_lean,
                    },
                }
                method_dict["params"].append(param_dict)

            data_dict["type"]["methods"].append(method_dict)

        return data_dict
