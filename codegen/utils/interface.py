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

    def to_dict(self: MethodParam):
        return {
            "name": self.name,
            "type": {
                "lean": self.type.lean,
                "cpp": self.type.cpp,
                "from_lean": self.type.from_lean,
            },
        }


@dataclass
class Method:
    kind: str
    lean: str
    cpp: str
    params: List[MethodParam]
    return_type: ReturnType

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "lean": self.lean,
            "cpp": self.cpp,
            "params": [param.to_dict() for param in self.params],
            "return_type": {
                "lean": self.return_type.lean,
                "cpp": self.return_type.cpp,
                "to_lean": self.return_type.to_lean,
            },
        }


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
        return {
            "namespace": self.namespace,
            "deps": self.deps,
            "type": {
                "lean": self.type.lean,
                "cpp": self.type.cpp,
                "methods": [method.to_dict() for method in self.type.methods],
            },
        }
