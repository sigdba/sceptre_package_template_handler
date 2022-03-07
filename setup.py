from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="sceptre_package_template_handler",
    version="0.0.0",
    author="Dan Boitnott",
    author_email="boitnott@sigcorp.com",
    description="A template handler for sceptre for downloadable packages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sigdba/sceptre_package_template_handler",
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    py_modules=["package_template_handler"],
    entry_points={
        "sceptre.template_handlers": [
            "package = package_template_handler:PackageTemplateHandler"
        ]
    },
)
