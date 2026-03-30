# Copyright 2025 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import argparse
import hashlib
import os
import shutil
import subprocess


def read_ensure_file(ensure_file_path: str):
    with open(ensure_file_path, "r") as f:
        content = f.read()

    subdirs = []
    for line in content.split(os.linesep):
        if line and line.startswith("@Subdir"):
            subdirs.append(line[8:])
    return subdirs


def make_archive(subdirs: list[str]):
    for subdir in subdirs:
        print(f'compressing {subdir.replace('/', '-')}.tar.gz')
        shutil.make_archive(subdir.replace("/", "-"), "gztar", subdir)


def generate_hash_file():
    for file in [file for file in os.listdir(".") if file.startswith("buildtools-")]:
        with open(file, "rb") as f:
            hash = hashlib.sha256(f.read()).hexdigest()
        with open("hash.md", "a") as f:
            f.write(f"{file}: {hash}\n")


def process_cipd_packages(ensure_files: str):
    _ensure_files = ensure_files.split(",")

    for ensure_file in _ensure_files:
        cmd = ['cipd', 'ensure', '-ensure-file', ensure_file, '-root', '.']
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(f'failed to run cipd ensure, original output:\n{e.output}')
            raise e

        subdirs = read_ensure_file(ensure_file)
        make_archive(subdirs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ensure-files", default="")
    parser.add_argument("--sha256-list", action="store_true", default=False)
    args = parser.parse_args()

    if args.ensure_files:
        process_cipd_packages(args.ensure_files)

    if args.sha256_list:
        generate_hash_file()


main()
