from setuptools import setup, find_packages

setup(
    name="oauth",
    version="1.0.0",
    packages=find_packages(include=["oauth", "oauth.*"]),  # ✅ Includes all package modules
    include_package_data=True,  # ✅ Ensures migrations and templates are included
    install_requires=[
        "asgiref==3.8.1",
        "certifi==2025.1.31",
        "charset-normalizer==3.4.1",
        "Django==5.1.7",
        "idna==3.10",
        "requests==2.32.3",
        "sqlparse==0.5.3",
        "tzdata==2025.1",
        "urllib3==2.3.0",
        "putils @ git+https://github.com/protellus/putils.git@0db043d85012dec3919488a279b5601d172c1046",  # ✅ External dependency
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    python_requires=">=3.8",
)
