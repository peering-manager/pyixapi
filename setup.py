from setuptools import find_packages, setup

setup(
    name="pyixapi",
    description="IX-API client library",
    url="https://github.com/peering-manager/pyixapi",
    author="Guillaume Mazoyer",
    author_email="oss@mazoyer.eu",
    license="Apache2",
    include_package_data=True,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=["requests>=2.20.0,<3.0", "PyJWT>=2.4.0,<2.5"],
    zip_safe=False,
    keywords=["ix-api", "internet-exchange", "peering"],
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
