import os
import platform
import json
import heapq
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from mkdocs.structure.files import Files

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


def is_excluded(path, exclude_list):
    if not exclude_list:
        return False
    for pattern in exclude_list:
        if pattern.endswith('*'):
            if path.startswith(pattern.partition('*')[0]):
                return True
        else:
            if path == pattern:
                return True
    return False

def get_git_first_commit_time(file_path):
    try:
        # git log --reverse --format="%aI" -- {file_path} | head -n 1
        cmd_list = ['git', 'log', '--reverse', '--format=%aI', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, encoding='utf-8')
        if process.returncode == 0 and process.stdout.strip():
            first_line = process.stdout.partition('\n')[0].strip()
            return datetime.fromisoformat(first_line)
    except Exception as e:
        logger.info(f"Error getting git first commit time for {file_path}: {e}")
    return None

def load_git_cache(docs_dir_path: Path):
    dates_cache = {}
    try:
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=docs_dir_path, encoding='utf-8'
        ).strip())
        rel_docs_path = docs_dir_path.relative_to(git_root).as_posix()

        cmd = ['git', 'log', '--reverse', '--no-merges', '--use-mailmap', '--name-only', '--format=%aN|%aE|%aI', f'--relative={rel_docs_path}', '--', '*.md']
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, encoding='utf-8')
        if process.returncode == 0:
            authors_dict = defaultdict(dict)
            first_commit = {}
            current_commit = None

            for line in process.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    # 使用元组，更轻量
                    current_commit = tuple(line.split('|', 2))
                elif line.endswith('.md') and current_commit:
                    name, email, created = current_commit
                    # 使用 defaultdict(dict)结构，处理有序与去重
                        # a.巧用 Python 字典的 setdefault 特性来去重（setdefault 为不存在的键提供初始值，不会覆盖已有值）
                        # b.巧用 Python 字典的插入顺序特性来保留内容插入顺序（Python 3.7+ 字典会保持插入顺序）
                    authors_dict[line].setdefault((name, email), None)
                    first_commit.setdefault(line, created)

            # 构建最终的缓存数据
            for file_path in first_commit:
                authors_list = [
                    {'name': name, 'email': email}
                    for name, email in authors_dict[file_path].keys()  # 这里的 keys() 是有序的
                ]
                dates_cache[file_path] = {
                    'created': first_commit[file_path],
                    'authors': authors_list
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

def get_recently_updated_files(docs_dir_path: Path, files: Files, exclude_list: list, limit: int = 10, recent_enable: bool = False):
    doc_mtime_map = {}
    try:
        # 1. 获取 git 信息，只记录已跟踪的文件最近一次的提交信息
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=docs_dir_path, encoding='utf-8'
        ).strip())
        rel_docs_path = docs_dir_path.relative_to(git_root).as_posix()

        cmd = ['git', 'log', '--no-merges', '--use-mailmap', '--format=%aN|%aE|%at', '--name-only', f'--relative={rel_docs_path}', '--', '*.md']
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, encoding='utf-8')
        if process.returncode == 0:
            result = subprocess.run(
                ["git", "ls-files", "*.md"],
                cwd=docs_dir_path, capture_output=True, encoding='utf-8'
            )
            tracked_files = set(result.stdout.splitlines()) if result.stdout else set()

            ts = None
            for line in process.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    ts = float(line.split('|')[2])
                elif line.endswith('.md') and line in tracked_files and ts:
                    # 只记录第一次出现的文件，即最近一次提交（setdefault 机制不会覆盖已有值）
                    doc_mtime_map.setdefault(line, ts)
    except Exception as e:
        logger.info(f"Error getting git tracked files in {docs_dir_path}: {e}")

    # 2. 构建所有文档的元数据
    recently_updated_results = []
    if recent_enable:
        files_meta = []
        for file in files:
            if not file.src_path.endswith('.md'):
                continue
            rel_path = getattr(file, 'src_uri', file.src_path)
            if os.sep != '/':
                rel_path = rel_path.replace(os.sep, '/')
            if is_excluded(rel_path, exclude_list):
                continue

            # 获取文档标题和 URL
            if file.page:
                # 过滤没有配置进导航里的文档
                if not file.page.title:
                    continue
                title, url = file.page.title, file.page.url
            else:
                title, url = file.name, file.url

            # 获取 git 记录的 mtime，没有则 fallback 到文件系统 mtime
            mtime = doc_mtime_map.get(rel_path, os.path.getmtime(file.abs_src_path))

            # 存储信息
            files_meta.append((mtime, rel_path, title, url))
            doc_mtime_map[rel_path] = mtime

        # 3. 构建最近更新列表
        if files_meta:
            # heapq 取 top limit
            top_results = heapq.nlargest(limit, files_meta, key=lambda x: x[0])
            recently_updated_results = [
                (datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"), *rest)
                for mtime, *rest in top_results
            ]

    return doc_mtime_map, recently_updated_results

def read_jsonl_cache(jsonl_file: Path):
    dates_cache = {}
    if jsonl_file.exists():
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
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
        with open(temp_file, 'w', encoding='utf-8') as f:
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
