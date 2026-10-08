#!/usr/bin/env python
# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Union

PROJECT_ROOT_ENV = "TOOLS_SHARED_PROJECT_ROOT"
PathLike = Union[str, os.PathLike]


def resolve_project_root(
    project_root: Optional[PathLike] = None,
    cwd: Optional[PathLike] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Path:
    """Resolve the host project root without relying on the package location."""
    if project_root:
        return Path(project_root).expanduser().resolve()

    environment = os.environ if environ is None else environ
    configured_root = environment.get(PROJECT_ROOT_ENV)
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    working_directory = Path.cwd() if cwd is None else Path(cwd)
    working_directory = working_directory.expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(working_directory), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return working_directory


@dataclass(frozen=True)
class ToolContext:
    tools_shared_root: Path
    project_root: Path

    @classmethod
    def create(cls, project_root: Optional[PathLike] = None) -> "ToolContext":
        return cls(
            tools_shared_root=Path(__file__).resolve().parent,
            project_root=resolve_project_root(project_root),
        )

    @property
    def tools_shared_buildtools_dir(self) -> Path:
        return self.tools_shared_root / "buildtools"

    @property
    def project_buildtools_dir(self) -> Path:
        return self.project_root / "buildtools"


_DEFAULT_CONTEXT = ToolContext.create()


class Env:
    TOOLS_SHARED_ROOT = str(_DEFAULT_CONTEXT.tools_shared_root)
    PROJECT_ROOT = str(_DEFAULT_CONTEXT.project_root)
    TOOLS_SHARED_BUILD_TOOLS_PATH = str(
        _DEFAULT_CONTEXT.tools_shared_buildtools_dir
    )
    PROJECT_BUILD_TOOLS_PATH = str(_DEFAULT_CONTEXT.project_buildtools_dir)
    JAVA_LINT_CONFIG_PATH = str(
        _DEFAULT_CONTEXT.tools_shared_root / "checkers" / "java-lint-check"
    )
