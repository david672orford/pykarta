# https://packaging.python.org/tutorials/packaging-projects/

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyKarta",
    version="0.93",
    author="David Chappell",
    author_email="David.Chappell@trincoll.edu",
    description="Mapping library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/david672orford/pykarta",
    packages=setuptools.find_packages(),
	package_data={
		"pykarta":["draw/*.svg", "maps/layers/symbols/*.svg"],
	},
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
)

