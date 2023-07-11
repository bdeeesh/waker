import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="waker",
    version="0.0.1-alpha",
    author="osama mohsen",
    author_email="osama.emohsen@gmail.com",
    description="Package for Fermilab waker experiment in the recycler ring.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/bdeeesh/waker",
    packages=setuptools.find_packages(),
    install_requires=[
        # 'h5py',
        # 'numpy'
    ],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
