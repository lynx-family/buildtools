# Copyright 2026 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import sys
import unittest
from pathlib import Path
from unittest import mock

TOOLS_SHARED_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_SHARED_ROOT))

import gen_ios_pkg


class InstallBundleTest(unittest.TestCase):
    @mock.patch("gen_ios_pkg.run_command")
    def test_configures_install_path_before_bundle_install(self, run_command):
        gen_ios_pkg.install_bundle("/tmp/bundle cache")

        self.assertEqual(
            run_command.call_args_list,
            [
                mock.call(
                    "bundle config set --local path '/tmp/bundle cache'"
                ),
                mock.call(
                    "SDKROOT=/Library/Developer/CommandLineTools/SDKs/"
                    "MacOSX.sdk bundle install"
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
