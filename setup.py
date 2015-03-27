from setuptools import setup

NAME = "pysemantic"

setup(
    name=NAME,
    version='0.0.1',
    author='Jaidev Deshpande',
    author_email='jaidev@dataculture.in',
    entry_points={
        'console_scripts': ['semantic = pysemantic.cli:main'],
               },
    packages=['pysemantic'],
)
