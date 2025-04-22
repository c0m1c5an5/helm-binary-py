#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from textwrap import dedent

import requests
from configupdater import ConfigUpdater
from setup_logging import setup_logging

URL_PATTERNS = {
    'linux-arm': 'https://get.helm.sh/helm-%s-linux-arm.tar.gz',
    'linux-arm64': 'https://get.helm.sh/helm-%s-linux-arm64.tar.gz',
    'linux-riscv64': 'https://get.helm.sh/helm-%s-linux-riscv64.tar.gz',
    'linux-386': 'https://get.helm.sh/helm-%s-linux-386.tar.gz',
    'linux-amd64': 'https://get.helm.sh/helm-%s-linux-amd64.tar.gz',
    'linux-ppc64le': 'https://get.helm.sh/helm-%s-linux-ppc64le.tar.gz',
    'linux-s390x': 'https://get.helm.sh/helm-%s-linux-s390x.tar.gz',
    'darwin-arm64': 'https://get.helm.sh/helm-%s-darwin-arm64.tar.gz',
    'darwin-amd64': 'https://get.helm.sh/helm-%s-darwin-amd64.tar.gz',
    'windows-arm64': 'https://get.helm.sh/helm-%s-windows-arm64.zip',
    'windows-amd64': 'https://get.helm.sh/helm-%s-windows-amd64.zip',
}


def get_hash_from_url(url: str) -> str:
    response = requests.get(url, verify=True)
    response.raise_for_status()
    hash = response.text.split()[0]
    return hash


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

    data: dict[str, dict[str, str]] = {}
    for platform, url_pattern in URL_PATTERNS.items():
        url = url_pattern % version
        sha256_url = url + '.sha256sum'
        sha256 = get_hash_from_url(sha256_url)
        data[platform] = {
            'url': url,
            'sha256': sha256,
        }

    download_scripts = dedent(
        f"""
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "armv6hf"
        marker = sys_platform == "linux" and platform_machine == "armv7l"
        url = {data["linux-arm"]["url"]}
        sha256 = {data["linux-arm"]["sha256"]}
        extract = tar
        extract_path = linux-arm/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "aarch64"
        url = {data["linux-arm64"]["url"]}
        sha256 = {data["linux-arm64"]["sha256"]}
        extract = tar
        extract_path = linux-arm64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "riscv64"
        url = {data["linux-riscv64"]["url"]}
        sha256 = {data["linux-riscv64"]["sha256"]}
        extract = tar
        extract_path = linux-riscv64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "i386"
        marker = sys_platform == "linux" and platform_machine == "i686"
        url = {data["linux-386"]["url"]}
        sha256 = {data["linux-386"]["sha256"]}
        extract = tar
        extract_path = linux-386/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "x86_64"
        url = {data["linux-amd64"]["url"]}
        sha256 = {data["linux-amd64"]["sha256"]}
        extract = tar
        extract_path = linux-amd64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "ppc64"
        marker = sys_platform == "linux" and platform_machine == "ppc64le"
        url = {data["linux-ppc64le"]["url"]}
        sha256 = {data["linux-ppc64le"]["sha256"]}
        extract = tar
        extract_path = linux-ppc64le/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "linux" and platform_machine == "s390x"
        url = {data["linux-s390x"]["url"]}
        sha256 = {data["linux-s390x"]["sha256"]}
        extract = tar
        extract_path = linux-s390x/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "darwin" and platform_machine == "arm64"
        url = {data["darwin-arm64"]["url"]}
        sha256 = {data["darwin-arm64"]["sha256"]}
        extract = tar
        extract_path = darwin-arm64/helm
        [helm]
        group = helm-binary
        marker = sys_platform == "darwin" and platform_machine == "x86_64"
        url = {data["darwin-amd64"]["url"]}
        sha256 = {data["darwin-amd64"]["sha256"]}
        extract = tar
        extract_path = darwin-amd64/helm
        [helm.exe]
        group = helm-binary
        marker = sys_platform == "win32" and platform_machine == "AMD64"
        marker = sys_platform == "cygwin" and platform_machine == "x86_64"
        url = {data["windows-amd64"]["url"]}
        sha256 = {data["windows-amd64"]["sha256"]}
        extract = zip
        extract_path = windows-amd64/helm.exe
        [helm.exe]
        group = helm-binary
        marker = sys_platform == "win32" and platform_machine == "ARM64"
        marker = sys_platform == "cygwin" and platform_machine == "aarch64"
        url = {data["windows-arm64"]["url"]}
        sha256 = {data["windows-arm64"]["sha256"]}
        extract = zip
        extract_path = windows-arm64/helm.exe
        """,
    ).strip()

    config['setuptools_download']['download_scripts'].set_values(
        download_scripts.splitlines(),
    )
    config.update_file()

    return 0


if __name__ == '__main__':
    sys.exit(main())
