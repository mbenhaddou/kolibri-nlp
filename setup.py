import setuptools
from kolibri.version import __version__
with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="kolibri-nlp",
    version=__version__,
    author="Mohamed Ben Haddou",
    author_email="mbenhaddou@mentis.io",
    include_package_data=True,
    description="An NLP toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst', '*.json', '*.npy', '*.db'],
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)