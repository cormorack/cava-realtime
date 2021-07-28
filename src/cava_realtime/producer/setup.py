"""Setup cava-realtime producer."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    inst_reqs = f.readlines()

with open('requirements.txt') as f:
    test_reqs = f.readlines()

extra_reqs = {
    "test": test_reqs,
}


setup(
    name="cava_realtime.producer",
    version="0.1.0",
    description=u"The interactive oceans realtime server built on top of FastAPI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    author=u"Landung Setiawan",
    author_email="landungs@uw.edu",
    url="https://github.com/cormorack/cava-realtime",
    license="MIT",
    packages=find_namespace_packages(exclude=["tests*"]),
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    setup_requires=["setuptools>=45", "wheel", "setuptools_scm"],
    entry_points=dict(
        console_scripts=["crt-producer = cava_realtime.producer.main:app"]
    ),
)
