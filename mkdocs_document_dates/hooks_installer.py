import os
import sys
import logging
import subprocess
from pathlib import Path
import platform

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

def get_config_dir():
    if platform.system().lower().startswith('win'):
        return Path(os.getenv('APPDATA', str(Path.home() / 'AppData' / 'Roaming')))
    else:
        # 优先级：XDG_CONFIG_HOME > $HOME/.config > cwd/.config
        xdg_config = os.getenv('XDG_CONFIG_HOME')
        if xdg_config:
            return Path(xdg_config)
        home = os.getenv('HOME')
        if home:
            return Path(home) / '.config'
        return Path.cwd() / '.config'

def check_python_version(interpreter):
    try:
        result = subprocess.run(
            [interpreter, "-c", "import sys; print(sys.version_info >= (3, 7))"],
            capture_output=True, encoding='utf-8')
        if result.returncode == 0 and result.stdout.strip().lower() == 'true':
            return True
        else:
            logger.warning(f"Low python version, requires python_requires >=3.7")
    except Exception as e:
        logger.info(f"Failed to check {interpreter}: {str(e)}")
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
        logger.error(
            f"No permission to create directory: {config_dir}\n"
            "If running inside Docker, please set environment variable HOME=/docs "
            "or XDG_CONFIG_HOME to a writable path."
        )
    except Exception as e:
        logger.error(f"Failed to create directory {config_dir}: {str(e)}")
    return None

def install_hook_file(source_dir: Path, target_dir: Path):
    try:
        shebang = detect_python_interpreter()
        for item in source_dir.iterdir():
            # 跳过隐藏文件和目录
            if item.name.startswith('.') or not item.is_file():
                continue
            # 添加 shebang 行
            content = item.read_text(encoding='utf-8')
            if content.startswith('#!'):
                content = shebang + os.linesep + content[content.find('\n')+1:]
            else:
                content = shebang + os.linesep + content

            target_hook_path = target_dir / item.name
            target_hook_path.write_text(content, encoding='utf-8')
            os.chmod(target_hook_path, 0o755)

        return True
    except Exception as e:
        logger.error(f"Failed to create hook file {target_hook_path}: {str(e)}")
    return False

def configure_git_hooks(hooks_dir):
    try:
        # 配置自定义合并驱动
        # script_path = hooks_dir / 'json_merge_driver.py'
        # subprocess.run(['git', 'config', '--global', 'merge.custom_json_merge.name', 'Custom JSON merge driver'], check=True)
        # subprocess.run(['git', 'config', '--global', 'merge.custom_json_merge.driver', f'"{sys.executable}" "{script_path}" %O %A %B'], check=True)

        subprocess.run(['git', 'config', '--global', 'core.hooksPath', str(hooks_dir)], check=True)
        logger.info(f"Git hooks successfully installed in: {hooks_dir}")
        return True
    except Exception:
        logger.warning("Git not detected, using plugin in a no-Git environment")
    return False

def install():
    try:
        # 创建hooks目录
        target_dir = setup_hooks_directory()
        if not target_dir:
            return False

        # 安装hook文件
        source_dir = Path(__file__).parent / 'hooks'
        if not install_hook_file(source_dir, target_dir):
            return False

        # 配置git hooks路径
        return configure_git_hooks(target_dir)

    except Exception as e:
        logger.error(f"Unexpected error during hooks installation: {str(e)}")
        return False

if __name__ == '__main__':
    install()