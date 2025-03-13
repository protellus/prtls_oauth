from setuptools import setup, find_packages

setup(
    name="prtls_oauth",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(include=["prtls_oauth", "prtls_oauth.*"]), 
    include_package_data=True, 
    install_requires=[
        "asgiref==3.8.1",
        "certifi==2023.7.2",
        "charset-normalizer==3.2.0",
        "Django>=4.2.20,<5.1",
        "djangorestframework==3.14.0",
        "idna==3.4",
        "prtls-utils @ git+https://github.com/protellus/prtls-utils.git@main",
        "pytz==2023.3",
        "requests==2.32.0",
        "sqlparse==0.5.3",
        "tzdata==2025.1",
        "urllib3==1.26.16"
    ],
    extras_require={
        "dev": [
            "black",
            "pytest",
        ]
    },)
