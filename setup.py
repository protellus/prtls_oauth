from setuptools import setup, find_packages

setup(
    name="oauth",
    version="1.0.0",
    packages=find_packages(include=["oauth", "oauth.*"]), 
    include_package_data=True,
    install_requires=[
        "django>=3.2",
        "djangorestframework",
        "putils @ git+https://github.com/protellus/putils.git@main"
    ],
)