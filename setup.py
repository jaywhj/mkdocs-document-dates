from setuptools import setup, find_packages
from setuptools.command.install import install
import atexit

def trigger_hook_install():
    try:
        import os
        import sys
        package_path = os.path.abspath(os.path.dirname(__file__))
        if package_path not in sys.path:
            sys.path.insert(0, package_path)
        
        # from mkdocs_document_dates.hooks_installer import install
        # install()
        # import mkdocs_document_dates
        __import__('mkdocs_document_dates')
    except Exception as e:
        print(f"Warning: Failed to install Git hooks: {e}")

class CustomInstallCommand(install):
    def run(self):
        atexit.register(trigger_hook_install)
        install.run(self)

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A new generation MkDocs plugin for displaying exact meta-info of documents, such as creation time, last update time, authors, email, etc."

VERSION = '3.2.1'

setup(
    name="mkdocs-document-dates",
    version=VERSION,
    author="Aaron Wang",
    author_email="aaronwqt@gmail.com",
    license="MIT",
    description="A new generation MkDocs plugin for displaying exact meta-info of documents, such as creation time, last update time, authors, email, etc.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaywhj/mkdocs-document-dates",
    packages=find_packages(),
    install_requires=[
        'mkdocs>=1.1.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'install': CustomInstallCommand,
    },
    entry_points={
        'mkdocs.plugins': [
            'document-dates = mkdocs_document_dates.plugin:DocumentDatesPlugin',
        ],
        'console_scripts': [
            # 提供手动安装 hooks 的入口
            'mkdocs-document-dates-hooks=mkdocs_document_dates.hooks_installer:install'
        ],
    },
    package_data={
        'mkdocs_document_dates': [
            'hooks/*',
            'static/languages/*',
            'static/tippy/*',
            'static/core/*',
            'static/config/*'
        ],
    },
    python_requires=">=3.7",
)