from setuptools import setup, find_packages

setup(
    name="prtls_oauth",
    #version="1.0.4", # Added migrations and lazy loading model to prevent AppRegistryNotReady: Apps aren't loaded yet.
    #version="1.0.5",  # Token model is now lazy loaded as aproperty to prevent AppRegistryNotReady: Apps aren't loaded yet.
    version="1.0.15",  # Remove hardcode admin path
    packages=find_packages(include=["prtls_oauth", "prtls_oauth.*"]),  # ✅ Includes all package modules
    include_package_data=True,  # ✅ Ensures migrations and templates are included
    install_requires=[
        "asgiref==3.7.2",
        "certifi==2023.7.22",
        "charset-normalizer==3.2.0",
        "Django==3.2",
        "djangorestframework==3.14.0",
        "idna==3.4",
        "prtls_utils @ git+https://${GITHUB_TOKEN}@github.com/protellus/prtls-utils.git@main",
        "pytz==2023.3",
        "requests==2.31.0",
        "sqlparse==0.4.4",
        "tzdata==2025.1",
        "urllib3==1.26.16"
    ],
    extras_require={
        "dev": [
            "black",
            "pytest",
        ]
    },)
