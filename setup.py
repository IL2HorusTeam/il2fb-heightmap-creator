# coding: utf-8

import sys

from pathlib import Path
from setuptools import setup


__here__ = Path(__file__).parent.absolute()


def parse_requirements(file_path: Path):
    requirements, dependencies = [], []

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            if line.startswith("-e"):
                line = line.split(' ', 1)[1]
                dependencies.append(line)
                line = line.split("#egg=", 1)[1]
                requirements.append(line)
            elif line.startswith("-r"):
                name = Path(line.split(' ', 1)[1])
                path = file_path.parent / name
                subrequirements, subdependencies = parse_requirements(path)
                requirements.extend(subrequirements)
                dependencies.extend(subdependencies)
            else:
                requirements.append(line)

    return requirements, dependencies


README = open(__here__ / "README.rst").read()

REQUIREMENTS_FILE_NAME = (
    "dist-windows.txt"
    if sys.platform == "win32"
    else "dist.txt"
)
REQUIREMENTS_FILE_PATH = __here__ / "requirements" / REQUIREMENTS_FILE_NAME
REQUIREMENTS, DEPENDENCIES = parse_requirements(REQUIREMENTS_FILE_PATH)


setup(
    name="il2fb-ds-airbridge",
    version="1.0.0",
    description=(
        "Distributed creator of height maps for "
        "«IL-2 Sturmovik: Forgotten Battles»"
    ),
    license="MIT",
    url="https://github.com/IL2HorusTeam/il2fb-heightmap-creator",
    author="Alexander Oblovatniy",
    author_email="oblovatniy@gmail.com",
    packages=[
        "il2fb.maps.heightmaps",
    ],
    namespace_packages=[
        "il2fb",
        "il2fb.maps",
    ],
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCIES,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
    ],
    entry_points={
        'console_scripts': [
            'il2fb-heightmap-create=il2fb.maps.heightmaps.creation:main',
            'il2fb-heightmap-render=il2fb.maps.heightmaps.rendering:main',
        ],
    }
)
