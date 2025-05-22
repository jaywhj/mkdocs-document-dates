import os
import sys
import shutil
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

def install():
    try:
        # 检查 git 是否可用
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True, encoding='utf-8')
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("Git not detected, skip hooks installation")
            return False
        
        # 准备配置目录
        config_dir = get_config_dir() / 'mkdocs-document-dates' / 'hooks'
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logging.error(f"No permission to create directory: {config_dir}")
            return False
        except Exception as e:
            logging.error(f"Failed to create directory {config_dir}: {str(e)}")
            return False

        hook_path = config_dir / 'pre-commit'
        source_hook = Path(__file__).parent / 'hooks' / 'pre-commit'

        # 复制 hook 文件到配置目录
        try:
            shutil.copy2(source_hook, hook_path)
        except PermissionError:
            logging.error(f"No permission to copy file to: {hook_path}")
            return False
        except Exception as e:
            logging.error(f"Failed to copy file to {hook_path}: {str(e)}")
            return False

        # 设置文件权限
        try:
            os.chmod(config_dir, 0o755)
            os.chmod(hook_path, 0o755)
        except OSError as e:
            logging.warning(f"Failed to set file permissions: {str(e)}")

        # 配置全局 git hooks 路径
        try:
            subprocess.run(
                ['git', 'config', '--global', 'core.hooksPath', str(config_dir)],
                check=True,
                capture_output=True,
                encoding='utf-8'
            )
            logging.info(f"Git hooks successfully installed in: {config_dir}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set git hooks path: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error during hooks installation: {str(e)}")
        return False

if __name__ == '__main__':
    install()