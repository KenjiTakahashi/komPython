# -*- coding: utf-8 -*-


from distutils.core import setup


setup(
    name="client",
    version="0.1",
    author="Karol Woźniak",
    author_email="wozniakk@gmail.com",
    packages=["client"],
    scripts=["scripts/client"],
    url="http://fake.url",
    license="MIT",
    description="A strange game client...",
    long_description=open("README").read(),
    install_requires=["twisted"]
)
