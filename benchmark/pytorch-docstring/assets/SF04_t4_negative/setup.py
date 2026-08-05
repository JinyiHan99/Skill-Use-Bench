from setuptools import setup, find_packages
setup(
    name="torchvision-lite",
    version="0.3.1",
    packages=find_packages(),
    install_requires=["torch>=2.0", "torchvision>=0.15"],
)
