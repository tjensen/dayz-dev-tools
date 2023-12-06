import setuptools  # type: ignore[import-untyped]


setuptools.setup(
    ext_modules=[
        setuptools.Extension(
            name="dayz_dev_tools_ext",
            sources=[
                "src/dayz_dev_tools_ext.c"
            ]
        )
    ])
