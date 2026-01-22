from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
import os

# Get the current directory
here = os.path.abspath(os.path.dirname(__file__))

# EDSDK paths relative to project root
edsdk_root = os.path.join(here, "EDSDK")
edsdk_include_dir = os.path.join(edsdk_root, "Header")
edsdk_lib_dir = os.path.join(edsdk_root, "Library", "x86_64")

# Extension module
ext_modules = [
    Pybind11Extension(
        "src.camera.edsdk",
        [
            "bindings/edsdk_wrapper.cpp",
        ],
        include_dirs=[
            edsdk_include_dir,
        ],
        library_dirs=[
            edsdk_lib_dir,
        ],
        libraries=["EDSDK"],
        cxx_std=17,
        define_macros=[
            ("TARGET_OS_LINUX", "1"),
        ],
        extra_compile_args=[
            "-Wall",
            "-Wextra",
            "-O2",
        ],
        extra_link_args=[
            f"-Wl,-rpath,{edsdk_lib_dir}",
        ],
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
