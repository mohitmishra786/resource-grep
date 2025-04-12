from setuptools import setup, find_packages

setup(
    name="resource_crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.8.0,<2.9.0",
        "elasticsearch>=8.7.0",
        "twisted==22.10.0",
    ],
) 