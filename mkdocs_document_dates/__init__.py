"""MkDocs Document Dates Plugin."""

from .hooks_installer import install

# 在包被导入时自动执行 hooks 安装
install()