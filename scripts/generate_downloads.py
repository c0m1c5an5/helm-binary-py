#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Sequence
from textwrap import dedent

import requests
from configupdater import ConfigUpdater
from setup_logging import setup_logging

RELEASE_RE = re.compile(
    r'^- \[(?P<name>[^\]]+)\]\((?P<url>[^\(]+)\) \(\[checksum\]\([^\)]+\) \/ (?P<sha256>\w{64})\)$',  # noqa: E501
)


def extract_entries(lines) -> dict[str, dict[str, str]]:
    result = {}
    for line in lines:
        match = RELEASE_RE.match(line)
        if match:
            name = match.group('name')
            url = match.group('url')
            sha256 = match.group('sha256')
            result[name] = {
                'url': url,
                'sha256': sha256,
            }
    return result


def get_release_notes(release_tag: str) -> str:
    response = requests.get(
        f'https://api.github.com/repos/helm/helm/releases/tags/{release_tag}',
        verify=True,
    )
    json = response.json()
    body = json['body']
    if not isinstance(body, str):
        raise TypeError('Response body must be of type: str')
    return body


def main(argv: Sequence[str] | None = sys.argv[1:]) -> int:
    setup_logging()
    logger = logging.getLogger()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--tag',
        type=str,
        help='Helm tag to generate download config for.',
    )

    args = parser.parse_args(argv)
    logger.debug('Args: %s', args.__dict__)

    config = ConfigUpdater()
    config.read('setup.cfg')

    config_version = config['metadata']['version'].value
    if not isinstance(config_version, str):
        raise ValueError('Metadata version must be of type: str')

    config_tag = 'v' + config_version.removeprefix('v').split('-')[0]

    tag: str | None = args.tag
    version = tag if tag else config_tag

    lines = get_release_notes(version).splitlines()
    data = extract_entries(lines)

    download_scripts = dedent(
        f"""
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "armv6hf"
        marker = sys_platform == "linux" and platform_machine == "armv7l"
        url = {data["Linux arm"]["url"]}
        sha256 = {data["Linux arm"]["sha256"]}
        extract = tar
        extract_path = linux-arm/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "aarch64"
        url = {data["Linux arm64"]["url"]}
        sha256 = {data["Linux arm64"]["sha256"]}
        extract = tar
        extract_path = linux-arm64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "riscv64"
        url = {data["Linux riscv64"]["url"]}
        sha256 = {data["Linux riscv64"]["sha256"]}
        extract = tar
        extract_path = linux-riscv64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "i386"
        marker = sys_platform == "linux" and platform_machine == "i686"
        url = {data["Linux i386"]["url"]}
        sha256 = {data["Linux i386"]["sha256"]}
        extract = tar
        extract_path = linux-386/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "x86_64"
        url = {data["Linux amd64"]["url"]}
        sha256 = {data["Linux amd64"]["sha256"]}
        extract = tar
        extract_path = linux-amd64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "darwin" and platform_machine == "arm64"
        url = {data["MacOS arm64"]["url"]}
        sha256 = {data["MacOS arm64"]["sha256"]}
        extract = tar
        extract_path = darwin-arm64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "darwin" and platform_machine == "x86_64"
        url = {data["MacOS amd64"]["url"]}
        sha256 = {data["MacOS amd64"]["sha256"]}
        extract = tar
        extract_path = darwin-amd64/helm
        [helm.exe]
        group = helm-binary
        marker = sys_platform == "win32" and platform_machine == "AMD64"
        marker = sys_platform == "win32" and platform_machine == "ARM64"
        marker = sys_platform == "cygwin" and platform_machine == "x86_64"
        url = {data["Windows amd64"]["url"]}
        sha256 = {data["Windows amd64"]["sha256"]}
        extract = zip
        extract_path = windows-amd64/helm.exe
        """,
    ).strip()

    config['setuptools_download']['download_scripts'].set_values(
        download_scripts.splitlines(),
    )
    config.update_file()

    return 0


if __name__ == '__main__':
    sys.exit(main())
