from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_desc = fh.read()
setup(
    name='imagecaptioning-aeye',
    packages=find_packages(),
    version='0.1.6',
    description='The Image Captioning module for the A-eye project.',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    url='https://github.com/jjmachan/imagecaptioning-aeye',
    author='jjmachan',
    authon_email='jamesjithin97@gmail.com',
    license='MIT',
    classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
                ],
    python_requires='>=3.6',
)
