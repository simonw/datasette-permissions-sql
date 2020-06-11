from setuptools import setup
import os

VERSION = "0.1a"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-permissions-sql",
    description="Datasette plugin for configuring permission checks using SQL queries",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-permissions-sql",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_permissions_sql"],
    entry_points={"datasette": ["permissions_sql = datasette_permissions_sql"]},
    install_requires=["datasette",],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx", "sqlite-utils~=2.0"]},
    tests_require=["datasette-permissions-sql[test]"],
)
