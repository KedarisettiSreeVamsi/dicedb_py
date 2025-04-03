"""
Setup configuration for dicedb_py package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dicedb_py",
    version="1.0.4",
    author="DiceDB Contributors",
    author_email="info@dicedb.io",
    description="Python client for DiceDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dicedb/dicedb-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)