{
  description = "Python development environment with GTK4";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3Packages;

        pythonDeps = with pythonPackages; [
          # Core Python packages
          pip
          setuptools
          wheel

          # GTK4 Python bindings
          pygobject3
          pycairo

          # C++/Python binding tools
          cffi
          cython
          pybind11

          # Common development packages
          pytest
          black
          flake8
          mypy
          numpy
        ];

        systemDeps = with pkgs; [
          # GTK4 and dependencies
          gtk4
          gobject-introspection
          gdk-pixbuf
          pango
          cairo
          python3
          python3.pkgs.pygobject3

          # C++ development tools for Python bindings
          gcc
          cmake
          ninja
          pkg-config
          glib

          # Python binding libraries
          python3.pkgs.cffi
          python3.pkgs.cython
          python3.pkgs.setuptools
          python3.pkgs.wheel

          # Additional C++ tools
          gdb
          valgrind
          clang-tools
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = pythonDeps ++ systemDeps;

          shellHook = ''
            export PYTHONPATH="${pkgs.python3}/${pkgs.python3.sitePackages}:$PYTHONPATH"
            export GI_TYPELIB_PATH="${pkgs.gtk4}/lib/girepository-1.0:${pkgs.gdk-pixbuf}/lib/girepository-1.0:${pkgs.pango}/lib/girepository-1.0:${pkgs.cairo}/lib/girepository-1.0:$GI_TYPELIB_PATH"
            export LD_LIBRARY_PATH="${pkgs.gtk4}/lib:${pkgs.gdk-pixbuf}/lib:${pkgs.pango}/lib:${pkgs.cairo}/lib:$LD_LIBRARY_PATH"

            # EDSDK library paths
            export EDSDK_ROOT="$(pwd)/EDSDK"
            export LD_LIBRARY_PATH="$EDSDK_ROOT/Library/x86_64:$LD_LIBRARY_PATH"

            echo "Python + GTK4 + C++ bindings development environment ready"
            echo "Python version: $(python3 --version)"
            echo "GTK4 version: $(pkg-config --modversion gtk4)"
            echo "GCC version: $(gcc --version | head -n1)"
            echo "CMake version: $(cmake --version | head -n1)"
            echo "EDSDK library: $EDSDK_ROOT/Library/x86_64/libEDSDK.so"
          '';
        };
      }
    );
}
