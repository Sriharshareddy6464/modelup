from setuptools import setup, find_packages

setup(
    name="modelup",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
        "requests",
        "httpx",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "modelup=cli.main:app",
        ],
    },
    python_requires=">=3.10",
)