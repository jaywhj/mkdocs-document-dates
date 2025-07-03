import os
import platform
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

class Author:
    def __init__(self, name="", email="", **kwargs):
        self.name = name
        self.email = email
        # 扩展属性
        self.attributes = kwargs
    
    def __getattr__(self, name):
        return self.attributes.get(name)
    
    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            **self.attributes
        }


def get_file_creation_time(file_path):
    try:
        stat = os.stat(file_path)
        system = platform.system().lower()
        if system.startswith('win'):  # Windows
            return datetime.fromtimestamp(stat.st_ctime)
        elif system == 'darwin':  # macOS
            try:
                return datetime.fromtimestamp(stat.st_birthtime)
            except AttributeError:
                return datetime.fromtimestamp(stat.st_ctime)
        else:  # Linux, 没有创建时间，使用修改时间
            return datetime.fromtimestamp(stat.st_mtime)
    except (OSError, ValueError) as e:
        logger.error(f"Failed to get file creation time for {file_path}: {e}")
        return datetime.now()

def check_git_repo():
    try:
        check_git = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
        if check_git.returncode == 0:
            return True
    except Exception as e:
        logger.info(f"Not a Git repository: {str(e)}")
    return False

def get_git_first_commit_time(file_path):
    try:
        # git log --reverse --format="%aI" -- {file_path} | head -n 1
        cmd_list = ['git', 'log', '--reverse', '--format=%aI', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, text=True)
        if process.returncode == 0 and process.stdout.strip():
            first_line = process.stdout.partition('\n')[0].strip()
            return datetime.fromisoformat(first_line).replace(tzinfo=None)
    except Exception as e:
        logger.info(f"Error getting git first commit time for {file_path}: {e}")
    return None

def get_git_last_commit_time(file_path):
    try:
        cmd_list = ['git', 'log', '-1', '--format=%aI', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, text=True)
        if process.returncode == 0 and process.stdout.strip():
            git_time = process.stdout.strip()
            return datetime.fromisoformat(git_time).replace(tzinfo=None)
    except Exception as e:
        logger.info(f"Error getting git last commit time for {file_path}: {e}")
    return None

def get_git_authors(file_path):
    try:
        # 为了兼容性，不采用管道命令，在 python 中处理去重
        # git log --format="%an|%ae" -- {file_path} | sort | uniq
        # git log --format="%an|%ae" -- {file_path} | grep -vE "bot|noreply|ci|github-actions|dependabot|renovate" | sort | uniq
        cmd_list = ['git', 'log', '--format=%an|%ae', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, text=True)
        if process.returncode == 0 and process.stdout.strip():
            # 使用字典去重和存储作者
            authors_map = {}
            for line in process.stdout.splitlines():
                if not line.strip() or line in authors_map:
                    continue
                name, email = line.split('|')
                authors_map[line] = Author(name=name, email=email)
            return list(authors_map.values()) or None
    except Exception as e:
        logger.warning(f"Failed to get git author info: {str(e)}")
    return None

def read_json_cache(cache_file: Path):
    dates_cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding='utf-8') as f:
                dates_cache = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading from '.dates_cache.json': {str(e)}")
    return dates_cache

def read_jsonl_cache(jsonl_file: Path):
    dates_cache = {}
    if jsonl_file.exists():
        try:
            with open(jsonl_file, "r", encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry and isinstance(entry, dict) and len(entry) == 1:
                            file_path, file_info = next(iter(entry.items()))
                            dates_cache[file_path] = file_info
                    except (json.JSONDecodeError, StopIteration) as e:
                        logger.warning(f"Skipping invalid JSONL line: {e}")
        except IOError as e:
            logger.warning(f"Error reading from '.dates_cache.jsonl': {str(e)}")
    return dates_cache

def write_jsonl_cache(jsonl_file: Path, dates_cache, tracked_files):
    try:
        # 使用临时文件写入，然后替换原文件，避免写入过程中的问题
        temp_file = jsonl_file.with_suffix('.jsonl.tmp')
        with open(temp_file, "w", encoding='utf-8') as f:
            for file_path in tracked_files:
                if file_path in dates_cache:
                    entry = {file_path: dates_cache[file_path]}
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # 替换原文件
        temp_file.replace(jsonl_file)
        
        # 将文件添加到git
        subprocess.run(["git", "add", str(jsonl_file)], check=True)
        logger.info(f"Successfully updated JSONL cache file: {jsonl_file}")
        return True
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to write JSONL cache file {jsonl_file}: {e}")
    except Exception as e:
        logger.error(f"Failed to add JSONL cache file to git: {e}")
    return False
