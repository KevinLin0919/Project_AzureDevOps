from setuptools import find_packages, setup

setup(
    name="asgards",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "azure-devops>=7.1.0b4",
        "msrest>=0.7.1",
        "requests>=2.31",
    ],
    python_requires=">=3.11",
)
