#!/usr/bin/env python3
from __future__ import annotations

from setuptools.config.setupcfg import read_configuration

if __name__ == '__main__':
    version: str = read_configuration('setup.cfg')['metadata']['version']
    print(
        'v' + version.removeprefix('v'),
    )
