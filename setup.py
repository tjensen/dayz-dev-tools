from os import path
import setuptools  # type: ignore[import]


with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dayz-dev-tools",
    version="1.0.2",
    author="Tim Jensen",
    author_email="tim.l.jensen@gmail.com",
    description="Useful tools for DayZ mod developers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/tjensen/dayz-dev-tools",
    project_urls={
        "Source": "https://github.com/tjensen/dayz-dev-tools",
        "Tracker": "https://github.com/tjensen/dayz-dev-tools/issues"
    },
    keywords=["dayz", "tools", "pbo"],
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
    entry_points={
        "console_scripts": [
            "unpbo=dayz_dev_tools.unpbo:main"
        ]
    })
