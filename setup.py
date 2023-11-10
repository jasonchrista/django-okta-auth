import os

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import find_packages, setup


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ""


def get_readme():
    """Return the README file contents. Supports text,rst, and markdown"""
    for name in ("README", "README.rst", "README.md"):
        if os.path.exists(name):
            return read_file(name)
    return ""


setup(
    name="django-okta-authentication",
    version=__import__("okta_auth").get_version().replace(" ", "-"),
    url="https://github.com/jasonchrista/django-okta-auth",
    author="Jason Christa",
    author_email="jason@zeitcode.com",
    description="Authenticated users using Okta",
    long_description=get_readme(),
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=read_file("requirements.txt"),
    classifiers=[
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Framework :: Django",
        "Programming Language :: Python",
    ],
)
