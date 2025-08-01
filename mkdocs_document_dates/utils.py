import os
import platform
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


def get_git_first_commit_time(file_path):
    try:
        # git log --reverse --format="%aI" -- {file_path} | head -n 1
        cmd_list = ['git', 'log', '--reverse', '--format=%aI', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, text=True)
        if process.returncode == 0 and process.stdout.strip():
            first_line = process.stdout.partition('\n')[0].strip()
            return datetime.fromisoformat(first_line)
    except Exception as e:
        logger.info(f"Error getting git first commit time for {file_path}: {e}")
    return None

def load_git_cache(docs_dir_path: Path):
    dates_cache = {}
    try:
        cmd = ['git', 'log', '--reverse', '--no-merges', '--name-only', '--format=%an|%ae|%aI', '--', '*.md']
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, text=True)
        if process.returncode == 0:
            git_root = Path(subprocess.check_output(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=docs_dir_path,
                text=True, encoding='utf-8'
            ).strip())
            docs_prefix = docs_dir_path.relative_to(git_root).as_posix()

            authors_dict = defaultdict(set)
            first_commit = {}
            current_commit = None

            for line in process.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    name, email, created = line.split('|', 2)
                    current_commit = {'name': name, 'email': email, 'created': created}
                elif line.endswith('.md') and current_commit:
                    if line.startswith(docs_prefix + '/'):
                        line = line[len(docs_prefix) + 1:]
                    authors_dict[line].add((current_commit['name'], current_commit['email']))
                    if line not in first_commit:
                        first_commit[line] = current_commit['created']

            for file_path in sorted(first_commit):
                dates_cache[file_path] = {
                    'created': first_commit[file_path],
                    'authors': [
                        {'name': name, 'email': email}
                        for name, email in sorted(authors_dict[file_path])
                        ]
                }
    except Exception as e:
        logger.info(f"Error getting git info in {docs_dir_path}: {e}")
    return dates_cache

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
        logger.warning(f"Failed to write JSONL cache file {jsonl_file}: {e}")
    except Exception as e:
        logger.warning(f"Failed to add JSONL cache file to git: {e}")
    return False
