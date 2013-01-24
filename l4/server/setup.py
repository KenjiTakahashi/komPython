# -*- coding: utf-8 -*-


from distutils.core import setup


setup(
    name="server",
    version="0.1",
    author="Karol Woźniak",
    author_email="wozniakk@gmail.com",
    packages=["server"],
    scripts=["scripts/server", "scripts/controller"],
    url="http://fake.url",
    license="MIT",
    description="A server for an strange game...",
    long_description="N/A",
    install_requires=["twisted"]
)
