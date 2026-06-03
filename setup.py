from setuptools import setup, find_packages
import os
import re

with open("README.md", "r") as fs:
    long_description = fs.read()


def find_version(*file_paths):
    base_module_file = os.path.join(*file_paths)
    with open(base_module_file) as f:
        base_module_data = f.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", base_module_data, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="nornir_nokia",
    version=find_version("nornir_nokia", "__init__.py"),
    description="Nokia SR OS pySROS Plugins for Nornir",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Vicnz03/nornir_nokia",
    author="Vic Chen",
    author_email="vicnz03@hotmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    packages=find_packages(),
    install_requires=[
        "pysros>=26.3",
        "nornir>=3.0.0",
        "netmiko>=4.3.0",
    ],
)
