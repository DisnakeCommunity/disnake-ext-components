import re
import setuptools


with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()


with open("disnake/ext/components/__init__.py", encoding="utf-8") as f:
    match = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', 
        f.read(),
        re.M
    )
    if match:
        version = match.group(1)
    else:
        raise RuntimeError("Version has not been set.")


setuptools.setup(
    name="disnake-ext-components",
    author="Chromosomologist",
    url="https://github.com/Chromosomologist/disnake-ext-components",
    version=version,
    packages=["disnake.ext.components"],
    license="MIT",
    description="A component listener wrapper for disnake",
    install_requires=requirements,
    python_requires=">=3.8.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ]
)