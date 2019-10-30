from setuptools import setup, find_packages

setup(
    name="dompare",
    version="0.0.1",
    keywords=("dompare", "Linux", 'diff', 'directories'),
    description="A program to diff files in two directories",
    long_description="A program to diff files in two directories",
    license="MIT Licence",

    url="https://github.com/vra/dompare",
    author="Yunfeng Wang",
    author_email="wyf.brz@gmail.com",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[],

    scripts=[],
    entry_points={
        'console_scripts': [
            'dompare=dompare.__init__:main'
        ]
    }
)
