from setuptools import setup

setup(
    name="aiopulse",
    version="0.5",
    description="A library for bulk sending and processing of async requests",
    author="Bernardo Tonasse",
    author_email="btonasse@notyet.com",
    packages=["aiopulse"],
    install_requires=["aiohttp", "yarl", "pydantic"],
)
