import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="StreamPlayer",
    version="0.1.0",
    author="Andy Jacobsen",
    author_email="atze.danjo@gmail.com",
    description="A simple playout script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ajacobsen/streamplayer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ],
)