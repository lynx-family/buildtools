# Copyright 2026 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_SHARED_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_SHARED_ROOT))

from checkers.android_code_style_checker import AndroidCodeStyleChecker
from checkers.java_lint_checker import PMD_EXECUTABLE
from default_env import PROJECT_ROOT_ENV, Env, ToolContext, resolve_project_root
from gn_tools import gn_wrapper


class ResolveProjectRootTest(unittest.TestCase):
    def test_explicit_root_has_highest_priority(self):
        with tempfile.TemporaryDirectory() as explicit_root:
            resolved = resolve_project_root(
                explicit_root,
                environ={PROJECT_ROOT_ENV: "/ignored/environment/root"},
            )

        self.assertEqual(resolved, Path(explicit_root).resolve())

    def test_uses_environment_root(self):
        with tempfile.TemporaryDirectory() as environment_root:
            resolved = resolve_project_root(
                environ={PROJECT_ROOT_ENV: environment_root}
            )

        self.assertEqual(resolved, Path(environment_root).resolve())

    @mock.patch("default_env.subprocess.run")
    def test_discovers_root_from_current_git_workspace(self, run):
        with tempfile.TemporaryDirectory() as working_directory:
            project_root = Path(working_directory) / "project"
            run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=f"{project_root}\n", stderr=""
            )

            resolved = resolve_project_root(
                cwd=working_directory,
                environ={},
            )

        self.assertEqual(resolved, project_root.resolve())
        run.assert_called_once_with(
            [
                "git",
                "-C",
                str(Path(working_directory).resolve()),
                "rev-parse",
                "--show-toplevel",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    @mock.patch("default_env.subprocess.run")
    def test_falls_back_to_current_workspace_outside_git(self, run):
        run.side_effect = subprocess.CalledProcessError(128, ["git"])
        with tempfile.TemporaryDirectory() as working_directory:
            resolved = resolve_project_root(
                cwd=working_directory,
                environ={},
            )

        self.assertEqual(resolved, Path(working_directory).resolve())


class ToolContextTest(unittest.TestCase):
    def test_separates_tools_shared_and_project_paths(self):
        with tempfile.TemporaryDirectory() as project_root:
            context = ToolContext.create(project_root)

        self.assertEqual(context.tools_shared_root, TOOLS_SHARED_ROOT)
        self.assertEqual(context.project_root, Path(project_root).resolve())
        self.assertEqual(
            context.project_buildtools_dir,
            Path(project_root).resolve() / "buildtools",
        )

    def test_build_tools_are_loaded_from_project(self):
        self.assertEqual(
            AndroidCodeStyleChecker.TOOL_PATH,
            os.path.join(
                Env.PROJECT_BUILD_TOOLS_PATH,
                "checkstyle",
                "checkstyle.jar",
            ),
        )
        self.assertEqual(
            PMD_EXECUTABLE,
            os.path.join(
                Env.PROJECT_BUILD_TOOLS_PATH,
                "pmd",
                "bin",
                "run.sh",
            ),
        )


class GnWrapperTest(unittest.TestCase):
    @mock.patch("gn_tools.gn_wrapper.subprocess.call")
    def test_uses_explicit_gn_directory(self, call):
        call.return_value = 0
        with tempfile.TemporaryDirectory() as gn_directory:
            with mock.patch.object(
                sys,
                "argv",
                [
                    "gn_wrapper.py",
                    "--gn-dir",
                    gn_directory,
                    "gen",
                    "out/default",
                ],
            ):
                result = gn_wrapper.main()

        self.assertEqual(result, 0)
        command = call.call_args.args[0]
        expected_executable = os.path.join(gn_directory, "gn")
        self.assertEqual(command[0], expected_executable)


if __name__ == "__main__":
    unittest.main()
