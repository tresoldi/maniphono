"""Setup file."""

# TODO: properly list pytest

import glob
import pathlib

# Import Python standard libraries
from setuptools import find_packages, setup

# The directory containing this file
LOCAL_PATH = pathlib.Path(__file__).parent

# The text of the README file
README_FILE = (LOCAL_PATH / "README.md").read_text(encoding="utf-8")

# Load requirements, so they are listed in a single place
with open("requirements.txt", encoding="utf-8") as fp:
    install_requires = [dep.strip() for dep in fp.readlines()] + ["pytest"]

# Build (recursive) list of resource files
resource_files = {}
resource_files["distances"] = "distances/*"
resource_files["models"] = "models/*/*"
#for directory in glob.glob("models/*/"):
#    files = glob.glob(directory + "*")
#    resource_files.append((directory, files))
#resource_files += glob.glob("distances/*")

# This call to setup() does all the work
setup(
    author_email="tiago.tresoldi@lingfil.uu.se",
    author="Tiago Tresoldi",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
    description="Python library for the symbolic manipulation of phoneme representations",
    include_package_data=True,
    install_requires=install_requires,
    keywords=["phoneme", "phonology", "phonetics", "distinctive features"],
    license="MIT",
    long_description_content_type="text/markdown",
    long_description=README_FILE,
    name="maniphono",
    packages=find_packages(where="src"),
    package_data=resource_files,
    package_dir={"": "src"},
    python_requires=">=3.6",
    test_suite="tests",
    tests_require=[],
    url="https://github.com/tresoldi/maniphono",
    version="0.3.3",  # remember to sync with __init__.py
    zip_safe=False,
)
