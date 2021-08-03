"""Setup cava-realtime application."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi",
    "streamz",
    "confluent-kafka",
    "jinja2",
    "importlib_resources",
    "prometheus-fastapi-instrumentator",
]
extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
    "server": ["uvicorn[standard]>=0.12.0"],
}


setup(
    name="cava_realtime.application",
    version="0.1.0",
    description=u"The interactive oceans realtime server built on top of FastAPI",  # noqa
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
    package_data={"cava_realtime": ["application/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
