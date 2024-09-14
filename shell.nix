{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    # nativeBuildInputs is usually what you want -- tools you need to run
    nativeBuildInputs = with pkgs.buildPackages; [
      # main.py dependencies
      python311Packages.pyserial

      # Pico development dependencies
      cmake
      gcc-arm-embedded
    ];
}

