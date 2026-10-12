# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.
import optparse
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

TOOLS_SHARED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOLS_SHARED_DIR not in sys.path:
    sys.path.insert(0, TOOLS_SHARED_DIR)

import git_lynx  # noqa: E402
from checkers.checker import Checker  # noqa: E402
from utils.merge_request import MergeRequest  # noqa: E402


class MergeRequestBaseCommitTest(unittest.TestCase):
    def test_rejects_non_sha_revision(self):
        # Reject non-hex revisions, such as branch names, before running Git.
        mr = MergeRequest()
        with mock.patch.object(mr, "RunCommand") as run_command:
            with self.assertRaisesRegex(ValueError, "Invalid commit SHA"):
                mr.ResolveCommitSha("origin/main")
        run_command.assert_not_called()

    def test_get_files_since_commit(self):
        # Resolve a short SHA before listing files changed from the base to HEAD.
        # Exclude deletions while retaining added, copied, modified, renamed,
        # and type-changed files.
        mr = MergeRequest()
        full_sha = "abc1234" + "a" * 33
        with mock.patch.object(
            mr,
            "RunCommand",
            side_effect=[(full_sha + "\n", ""), ("a.cc\ndir/b.h\n", "")],
        ) as run_command:
            files = mr.GetFilesSinceCommit("abc1234")

        self.assertEqual(["a.cc", "dir/b.h"], files)
        self.assertEqual(
            ["git", "rev-parse", "--verify", "abc1234^{commit}"],
            run_command.call_args_list[0].args[0],
        )
        self.assertEqual(
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRT",
                full_sha,
                "HEAD",
                "--",
            ],
            run_command.call_args_list[1].args[0],
        )

    def test_get_lines_since_commit(self):
        # Use a zero-context diff from the base to HEAD and exclude deleted files.
        mr = MergeRequest()
        full_sha = "bcd2345" + "b" * 33
        diff = "diff --git a/a.cc b/a.cc\n"
        with mock.patch.object(
            mr, "RunCommand", side_effect=[(full_sha + "\n", ""), (diff, "")]
        ) as run_command:
            self.assertEqual(diff, mr.GetLinesSinceCommit("bcd2345"))

        self.assertEqual(
            [
                "git",
                "diff",
                "--diff-filter=ACMRT",
                "-U0",
                full_sha,
                "HEAD",
                "--",
            ],
            run_command.call_args_list[1].args[0],
        )

    def test_rejects_hex_ref_that_is_not_a_sha_prefix(self):
        # Reject a hex-only input when the resolved SHA does not start with it.
        # This prevents hex-named branches or tags from being accepted as SHAs.
        mr = MergeRequest()
        with mock.patch.object(mr, "RunCommand", return_value=("d" * 40 + "\n", "")):
            with self.assertRaisesRegex(ValueError, "Invalid commit SHA"):
                mr.ResolveCommitSha("abc1234")

    def test_run_command_reports_nonzero_exit_without_stderr(self):
        # Preserve the existing return interface while exposing a failed exit code.
        process = mock.Mock(returncode=128)
        process.communicate.return_value = (b"", b"")
        with mock.patch("utils.merge_request.subprocess.Popen", return_value=process):
            _, error = MergeRequest().RunCommand(["git", "diff"])
        self.assertEqual("Command failed with exit code 128", error)

    def test_get_files_since_commit_raises_on_diff_failure(self):
        # A failed file diff must not be converted into an empty file list.
        mr = MergeRequest()
        full_sha = "abc1234" + "a" * 33
        with mock.patch.object(
            mr,
            "RunCommand",
            side_effect=[(full_sha, ""), ("", "diff failed")],
        ):
            with self.assertRaisesRegex(RuntimeError, "diff failed"):
                mr.GetFilesSinceCommit("abc1234")

    def test_get_lines_since_commit_raises_on_diff_failure(self):
        # A failed line diff must not be converted into an empty diff.
        mr = MergeRequest()
        full_sha = "abc1234" + "a" * 33
        with mock.patch.object(
            mr,
            "RunCommand",
            side_effect=[(full_sha, ""), ("", "diff failed")],
        ):
            with self.assertRaisesRegex(RuntimeError, "diff failed"):
                mr.GetLinesSinceCommit("abc1234")


class CheckerBaseCommitTest(unittest.TestCase):
    def test_uses_base_commit_diff(self):
        # Read the requested commit range instead of the last-commit diff.
        checker = Checker()
        checker.check_changed_lines = mock.Mock(return_value="passed")
        options = SimpleNamespace(
            all=False,
            changed=False,
            base_commit="c" * 40,
            verbose=False,
        )
        mr = mock.Mock()
        mr.GetLinesSinceCommit.return_value = ""

        checker.run(options, mr, ["a.cc"])

        mr.GetLinesSinceCommit.assert_called_once_with("c" * 40)
        mr.GetLastCommitLines.assert_not_called()


class CheckOptionsTest(unittest.TestCase):
    def test_base_commit_conflicts_with_changed(self):
        # Reject --base-commit with --changed because they select different diffs.
        with self.assertRaises(SystemExit):
            git_lynx.CMDcheck(
                optparse.OptionParser(),
                ["--base-commit", "abc1234", "--changed"],
            )

    def test_base_commit_conflicts_with_all(self):
        # Reject the incremental --base-commit mode with the full --all mode.
        with self.assertRaises(SystemExit):
            git_lynx.CMDcheck(
                optparse.OptionParser(),
                ["--base-commit", "abc1234", "--all"],
            )


if __name__ == "__main__":
    unittest.main()
