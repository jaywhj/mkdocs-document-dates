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

def detect_python_interpreter():
    # 尝试python3
    try:
        result = subprocess.run(
            ["python3", "-c", "import sys; print(sys.version_info >= (3, 7))"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip() == 'True':
            return '#!/usr/bin/env python3'
        else:
            logging.warning(f"Low python version, requires python_requires >=3.7")
    except Exception as e:
        logging.debug(f"Failed to check python3: {str(e)}")
    
    # 尝试python
    try:
        result = subprocess.run(
            ["python", "-c", "import sys; print(sys.version_info >= (3, 7))"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip() == 'True':
            return '#!/usr/bin/env python'
        else:
            logging.warning(f"Low python version, requires python_requires >=3.7")
    except Exception as e:
        logging.debug(f"Failed to check python: {str(e)}")
    
    # 使用当前运行的Python解释器
    return f'#!{sys.executable}'

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

        # 检测Python解释器并获取合适的shebang行
        shebang = detect_python_interpreter()
        logging.info(f"Using shebang: {shebang}")

        # 安装钩子文件
        hooks_installed = False
        source_hooks_dir = Path(__file__).parent / 'hooks'
        for hook_file in source_hooks_dir.glob('*'):
            if hook_file.is_file() and not hook_file.name.startswith('.'):
                target_hook_path = config_dir / hook_file.name
                try:
                    # 读取源文件内容
                    with open(hook_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    
                    # 修改shebang行
                    if content.startswith('#!'):
                        content = shebang + os.linesep + content[content.find('\n'):]
                    else:
                        content = shebang + os.linesep + content

                    # 直接写入目标文件
                    with open(target_hook_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(content)
                    
                    # 设置执行权限
                    os.chmod(target_hook_path, 0o755)
                    hooks_installed = True
                    logging.info(f"Created hook with custom shebang: {hook_file.name}")
                except Exception as e:
                    logging.error(f"Failed to create file {target_hook_path}: {str(e)}")
                    return False

        if not hooks_installed:
            logging.warning("No hook files found, the hooks installation failed")
            return False

        # 设置目录权限
        try:
            os.chmod(config_dir, 0o755)
        except OSError as e:
            logging.warning(f"Failed to set directory permissions: {str(e)}")

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