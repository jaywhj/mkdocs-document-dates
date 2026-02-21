from setuptools import find_packages, setup


def legacy_setup():
    setup(
        name="mkdocs-document-dates",
        version="3.7.0",
        author="Aaron Wang",
        author_email="aaronwqt@gmail.com",
        license="MIT",
        description="A new generation MkDocs plugin for displaying exact creation date, last updated date, authors, email of documents",
        long_description=open("README.md", encoding="utf-8").read(),
        long_description_content_type="text/markdown",
        url="https://github.com/jaywhj/mkdocs-document-dates",
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            "mkdocs>=1.1.0",
        ],
        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ],
        entry_points={
            "mkdocs.plugins": [
                "document-dates = mkdocs_document_dates.plugin:DocumentDatesPlugin",
            ],
            "console_scripts": [
                "mkdocs-document-dates-hooks=mkdocs_document_dates.hooks_installer:install",
                "mdd-hooks=mkdocs_document_dates.hooks_installer:install",
            ],
        },
        package_data={
            "mkdocs_document_dates": [
                "hooks/*",
                "static/templates/*",
                "static/fonts/*",
                "static/tippy/*",
                "static/core/*",
                "static/config/*"
            ],
        },
        python_requires=">=3.7",
    )


try:
    setup()
except Exception:
    legacy_setup()
