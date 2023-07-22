from setuptools import setup, find_packages

setup(
    name="dompare",
    version="0.2.1",
    keywords=("dompare", "Linux", "diff", "directories"),
    description="A program to diff two directories recursively",
    long_description="dompare is  program to diff same name iles in two directories recursively",
    license="MIT Licence",
    url="https://github.com/vra/dompare",
    author="Yunfeng Wang",
    author_email="wyf.brz@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[
        "binaryornot>=0.4.4",
        "loguru",
    ],
    scripts=[],
    entry_points={"console_scripts": ["dompare=dompare.__init__:main"]},
)
