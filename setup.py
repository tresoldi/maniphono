import pathlib
from setuptools import setup, find_packages

# The directory containing this file
LOCAL_PATH = pathlib.Path(__file__).parent

# The text of the README file
README_FILE = (LOCAL_PATH / "README.md").read_text()


# Load requirements, so they are listed in a single place
with open("requirements.txt") as fp:
    install_requires = [dep.strip() for dep in fp.readlines()]

# This call to setup() does all the work
setup(
    author_email="tresoldi@shh.mpg.de",
    author="Tiago Tresoldi",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
    description="Python library for the symbolic manipulation of phoneme representations",
    entry_points={"console_scripts": ["maniphono=maniphono.__main__:main"]},
    include_package_data=True,
    install_requires=install_requires,
    keywords=["phoneme", "phonology", "phonetics", "distinctive features"],
    license="MIT",
    long_description_content_type="text/markdown",
    long_description=README_FILE,
    name="maniphono",
    packages=["maniphono", "models"],
    python_requires=">=3.7",
    test_suite="tests",
    tests_require=[],
    url="https://github.com/tresoldi/maniphono",
    version="0.2.1",  # remember to sync with __init__.py
    zip_safe=False,
)
