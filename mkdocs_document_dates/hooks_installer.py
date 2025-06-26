import os
import sys
import logging
import subprocess
from pathlib import Path
import platform

# 配置日志等级 (INFO WARNING ERROR)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

def get_config_dir():
    if platform.system().lower().startswith('win'):
        return Path(os.getenv('APPDATA', str(Path.home() / 'AppData' / 'Roaming')))
    else:
        return Path.home() / '.config'

def check_python_version(interpreter):
    try:
        result = subprocess.run(
            [interpreter, "-c", "import sys; print(sys.version_info >= (3, 7))"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip().lower() == 'true':
            return True
        else:
            logging.warning(f"Low python version, requires python_requires >=3.7")
            return False
    except Exception as e:
        logging.debug(f"Failed to check {interpreter}: {str(e)}")
        return False

def detect_python_interpreter():
    # 检查可能的Python解释器
    python_interpreters = ['python3', 'python']
    
    for interpreter in python_interpreters:
        if check_python_version(interpreter):
            return f'#!/usr/bin/env {interpreter}'
    
    # 如果都失败了，使用当前运行的Python解释器
    return f'#!{sys.executable}'

def setup_hooks_directory():
    config_dir = get_config_dir() / 'mkdocs-document-dates' / 'hooks'
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(config_dir, 0o755)
        return config_dir
    except PermissionError:
        logging.error(f"No permission to create directory: {config_dir}")
        return None
    except Exception as e:
        logging.error(f"Failed to create directory {config_dir}: {str(e)}")
        return None

def install_hook_file(source_hook, target_dir):
    target_hook_path = target_dir / source_hook.name
    try:
        # 读取并更新hook文件内容
        with open(source_hook, 'r', encoding='utf-8') as f_in:
            content = f_in.read()
        
        # 更新shebang行
        shebang = detect_python_interpreter()
        if content.startswith('#!'):
            content = shebang + os.linesep + content[content.find('\n'):]
        else:
            content = shebang + os.linesep + content
        
        # 写入并设置权限
        with open(target_hook_path, 'w', encoding='utf-8') as f_out:
            f_out.write(content)
        os.chmod(target_hook_path, 0o755)
        return True
    except Exception as e:
        logging.error(f"Failed to create hook file {target_hook_path}: {str(e)}")
        return False

def configure_git_hooks(hooks_dir):
    try:
        subprocess.run(
            ['git', 'config', '--global', 'core.hooksPath', str(hooks_dir)],
            check=True, capture_output=True, encoding='utf-8'
        )
        logging.info(f"Git hooks successfully installed in: {hooks_dir}")
        return True
    except Exception:
        logging.warning("Git not detected, failed to set git hooks path")
        return False

def install():
    try:
        # 创建hooks目录
        hooks_dir = setup_hooks_directory()
        if not hooks_dir:
            return False

        # 安装hook文件
        source_hook = Path(__file__).parent / 'hooks' / 'pre-commit'
        if not install_hook_file(source_hook, hooks_dir):
            return False

        # 配置git hooks路径
        return configure_git_hooks(hooks_dir)

    except Exception as e:
        logging.error(f"Unexpected error during hooks installation: {str(e)}")
        return False

if __name__ == '__main__':
    install()