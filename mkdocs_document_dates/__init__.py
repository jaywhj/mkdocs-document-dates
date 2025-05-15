"""MkDocs Document Dates Plugin."""

from .hooks_installer import install

# 在包被导入时自动执行 hooks 安装
try:
    result = install()
    if not result:
        print("Tip: Git hooks installation was skipped (probably because Git was not detected or not in the Git repository)")
except Exception as e:
    print(f"Warning: Git hooks installation failed: {e}")