{
  description = "Jasmin compiler for cryptography assignments";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Pin nixpkgs for ARM GCC 13.3.rel1 (compatible with Jasmin output)
    nixpkgs-gcc13.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, nixpkgs-gcc13, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pkgs-gcc13 = nixpkgs-gcc13.legacyPackages.${system};

        jasmin-src = pkgs.fetchFromGitHub {
    owner = "jasmin-lang";
    repo = "jasmin";
    rev = "50bdec64245b9d791dc7676cfa7ad33c5c0d70a7";
    hash = "sha256-ET1BPKsb++nAyYVFqtNTQ9StLT9KxXH9cpkhNkFiZsc=";
  };

  jasmin-drv = pkgs.callPackage "${jasmin-src}/default.nix" { };
  jasmin-compiler = jasmin-drv.overrideAttrs {
    name = "jasmin";
    buildPhase = ''
      make -C compiler/ CIL
      make -C compiler/
    '';
  };

      in {
        packages = {
          default = jasmin-compiler;
          jasmin-compiler = jasmin-compiler;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            # Jasmin compiler
            jasmin-compiler

            # Build tools
            pkgs.gnumake
            pkgs.gcc

            # ARM toolchain (use version 13.3.rel1 from nixos-24.11)
            pkgs-gcc13.gcc-arm-embedded-13

            # Flashing and debugging
            pkgs.openocd

            # QEMU for ARM emulation
            pkgs.qemu

            # Linting and formatting tools
            pkgs.pre-commit
            pkgs.clang-tools

            # Python and packages
            (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
              pyserial
              tqdm
              pytest
              black
              flake8
            ]))
          ];

          shellHook = ''
            echo "Jasmin compiler environment loaded"
            echo "jasminc available at: $(which jasminc)"
            echo ""
            echo "Available tools:"
            echo "  - ARM GCC: $(arm-none-eabi-gcc --version | head -n1)"
            echo "  - OpenOCD: $(openocd --version 2>&1 | head -n1)"
            echo "  - QEMU: $(qemu-system-arm --version | head -n1)"
            echo "  - Python: $(python3 --version)"
            echo ""
            echo "Platform options:"
            echo "  - Physical board: make (default)"
            echo "  - QEMU emulation: make PLATFORM=qemu"
            echo ""
          '';
        };
      });
}
