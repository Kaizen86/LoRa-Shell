#!/usr/bin/env bash

# Check if the path to the SDK directory hasn't already been set
# This will override the default listed in CMakeLists.txt
if [ -z "$PICO_SDK_PATH" ]; then
  # Make sure to change this to point at your SDK directory!
  export PICO_SDK_PATH="`pwd`/../../pico-sdk"
fi
# Verify the specified folder exists
if [ ! -d "$PICO_SDK_PATH" ]; then
  echo PICO_SDK_PATH is invalid!
  echo Current value is \'"$PICO_SDK_PATH"\'
  exit 1
fi

# Create build output directory
mkcd() { mkdir -p "$@" && cd "$@"; }
mkcd build

# Run CMake compiler
cmake ..
# Check if cmake succeeded
if [ $? -ne 0 ]; then
  echo "Build fail: cmake error!"
  exit 1
fi

make lora_chat
if [ $? -ne 0 ]; then
  echo "Build fail: make error!"
  exit 1
fi

echo "Build finished OK"
