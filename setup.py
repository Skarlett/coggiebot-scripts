#!/usr/bin/env python3
from setuptools import setup, find_packages
setup(
    name="deemix-stream",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "deemix",
        "requests",
        "spotipy",
        "click",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "deemix-stream=deemix_stream.__main__:stream_cli",
            "deemix-metadata=deemix_stream.__main__:metadata_cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
