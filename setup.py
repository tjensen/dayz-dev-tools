from os import path
import setuptools  # type: ignore[import]
import typing


with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), "r", encoding="utf8") as fh:
    long_description = fh.read()

with open(path.join("dayz_dev_tools", "__init__.py")) as f:
    ns: typing.Dict[str, str] = {}
    exec(f.read(), ns)
    version = ns["version"]

setuptools.setup(
    name="dayz-dev-tools",
    version=version,
    author="Tim Jensen",
    author_email="tim.l.jensen@gmail.com",
    description="Useful tools for DayZ mod developers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://dayz-dev-tools.readthedocs.io/",
    project_urls={
        "Source": "https://github.com/tjensen/dayz-dev-tools",
        "Tracker": "https://github.com/tjensen/dayz-dev-tools/issues"
    },
    keywords=["dayz", "tools", "pbo", "server"],
    packages=["dayz_dev_tools"],
    package_data={
        "dayz_dev_tools": ["py.typed"]  # PEP 561
    },
    zip_safe=False,  # Enables mypy to find the installed package
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Games/Entertainment :: First Person Shooters",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
        "Typing :: Typed"
    ],
    python_requires=">=3.8",
    setup_requires=["wheel"],
    install_requires=[
        "jsonschema>=3.2.0",
        "toml>=0.10.2"
    ],
    entry_points={
        "console_scripts": [
            "unpbo=dayz_dev_tools.unpbo:main",
            "run-server=dayz_dev_tools.run_server:main"
        ]
    },
    ext_modules=[
        setuptools.Extension(
            name="dayz_dev_tools_ext",
            sources=[
                "src/dayz_dev_tools_ext.c"
            ]
        )
    ])
