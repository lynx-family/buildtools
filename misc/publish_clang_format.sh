#!/bin/bash
# Copyright 2025 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

# This script is used to extract clang-format executable file from llvm package

root_dir=$PWD

# clear the hash.md
cat /dev/null > hash.md

# Traverse all tar.gz under llvm directory 
for file in buildtools-*.tar.gz;do
    # llvm files already exists
    raw_folder=$(echo $file | sed 's/.tar.gz//g')
    
    # extract the clang-format file
    clang_format_dir=$(echo $raw_folder | sed 's/llvm/clang-format/g')
    mkdir $clang_format_dir
    subdir=$(echo $raw_folder | awk -F"-" '{print $(NF-1)"-"$NF}')
    clang_format_file=""
    if [ -f "$root_dir/buildtools/llvm/${subdir}/bin/clang-format.exe" ]; then
        clang_format_file="clang-format.exe"
    elif [ -f "$root_dir/buildtools/llvm/${subdir}/bin/clang-format" ]; then
        clang_format_file="clang-format"
    else
        echo "clang-format not found"
        continue
    fi
    cp $root_dir/buildtools/llvm/$subdir/bin/$clang_format_file $clang_format_dir/
    
    # package the artifacts
    tar -czf $clang_format_dir.tar.gz $clang_format_dir

    # get the hash of file and write in hash.md
    hash=$(openssl dgst -sha256 "$clang_format_dir.tar.gz" | awk '{print $2}')
    echo "$clang_format_dir.tar.gz: $hash" - >> hash.md

    # delete llvm packages
    rm -rf $file
done

echo "Extraction and archiving completed."
