from os import path
import setuptools  # type: ignore[import-untyped]


with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), "r", encoding="utf8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="dayz-dev-tools",
    version="1.6.0",
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: First Person Shooters",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
        "Typing :: Typed"
    ],
    python_requires=">=3.8",
    setup_requires=["wheel"],
    install_requires=[
        "pydantic>=2.5.0",
        "tomli>=2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "unpbo=dayz_dev_tools.unpbo:main",
            "run-server=dayz_dev_tools.run_server:main",
            "guid=dayz_dev_tools.guid:main"
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
