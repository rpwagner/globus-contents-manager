from setuptools import setup
from setuptools import find_packages

def readme():
    """Reads the README.md file to use as the 'long description'"""
    with open('README.md') as f:
        return f.read()

def requirements():
    """
    Reads the requirements.txt file in order to extract requirements
    that need to be installed
    """
    with open('requirements.txt') as f:
        return f.read()

setup(
    name='globuscontents',
    version='0.1',
    description='A Globus Contents Manager',
    long_description=readme(),
    url='http://github.com/gneezyn/globus-contents-manager',
    author='Netta Gneezy',
    author_email='netta.en@gmail.com',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=requirements().splitlines(),
    zip_safe=False
)
