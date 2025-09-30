import os
import platform
import json
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
            docs_prefix_with_slash = docs_prefix + '/'
            prefix_len = len(docs_prefix_with_slash)

            authors_dict = defaultdict(dict)
            first_commit = {}
            current_commit = None

            for line in process.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    name, email, created = line.split('|', 2)
                    # 使用元组，更轻量
                    current_commit = (name, email, created)
                elif line.endswith('.md') and current_commit:
                    if line.startswith(docs_prefix_with_slash):
                        line = line[prefix_len:]
                    # 解构元组，避免字典查找
                    name, email, created = current_commit
                    # 使用有序去重结构，保持作者首次出现的顺序（Python 3.7+：字典会保持插入顺序）
                    authors_dict[line].setdefault((name, email), None)
                    if line not in first_commit:
                        first_commit[line] = created

            # 构建最终的缓存数据
            for file_path in first_commit:
                authors_list = [
                    {'name': name, 'email': email}
                    for name, email in authors_dict[file_path].keys()
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
    doc_to_time_map = {}
    git_files = {}
    try:
        # 从 git log 中获取已跟踪的 markdown 文件详情
        cmd = ['git', 'log', '--no-merges', '--name-only', '--format=%an|%ae|%at', '--', '*.md']
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, text=True)
        if process.returncode == 0:
            # 获取 git 已跟踪的(tracked) markdown 文件列表
            cmd = ["git", "ls-files", "*.md"]
            result = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, text=True)
            tracked_files = set(result.stdout.splitlines()) if result.stdout else set()

            # 处理文档前缀
            git_root = Path(subprocess.check_output(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=docs_dir_path,
                text=True,
                encoding='utf-8'
            ).strip())
            docs_prefix = docs_dir_path.relative_to(git_root).as_posix()
            docs_prefix_with_slash = docs_prefix + '/'
            prefix_len = len(docs_prefix_with_slash)

            # 用于去重的文档集合
            unique_docs = set()
            current_time = None
            current_docs = []

            def process_current_time_docs():
                if current_time and current_docs:
                    last_commit_time = current_time.split('|')[2];
                    for doc in current_docs:
                        # 过滤未跟踪的(untracked) markdown 文件
                        if doc not in tracked_files:
                            continue

                        mtime = float(last_commit_time)
                        # 存储：文档-最后修改时间映射
                        doc_to_time_map[doc] = mtime

                        # 最后更新文档列表：过滤要排除的文档
                        if is_excluded(doc, exclude_list):
                            continue

                        # 获取文档详情
                        file = files.get_file_from_path(doc)
                        if not file:
                            continue
                        if file.page:
                            # 最后更新文档列表：过滤没有配置进导航里的文档
                            if not file.page.title:
                                continue
                            title, url = file.page.title, file.page.url
                        else:
                            title, url = file.name, file.url

                        # 存储：最后更新文档列表
                        git_files[doc] = (mtime, doc, title, url)

            for line in process.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    # 处理前一个时间点的文档
                    process_current_time_docs()
                    current_time = line
                    current_docs = []
                elif line.endswith('.md'):
                    if line.startswith(docs_prefix_with_slash):
                        line = line[prefix_len:]
                    if line not in unique_docs:
                        unique_docs.add(line)
                        current_docs.append(line)
            # 处理最后一组数据
            process_current_time_docs()

    except Exception as e:
        logger.info(f"Error getting recently updated docs in {docs_dir_path}: {e}")

    # 将 git 已跟踪的 markdown 文件详情 与 本地文件系统的文件详情 合并
    recently_updated_results = []
    if recent_enable:
        recently_updated_results = get_recently_modified_files(files, git_files, exclude_list, limit)
    return doc_to_time_map, recently_updated_results

def get_recently_modified_files(files: Files, git_files: dict, exclude_list: list, limit: int = 10):
    if not files:
        return []
    temp_results = []
    for file in files:
        if not file.src_path.endswith('.md'):
            continue
        rel_path = getattr(file, 'src_uri', file.src_path)
        if os.sep != '/':
            rel_path = rel_path.replace(os.sep, '/')

        if rel_path in git_files:
            temp_results.append(git_files[rel_path])
        else:
            if is_excluded(rel_path, exclude_list):
                continue
            if file.page:
                # 过滤没有配置进导航里的文档
                if not file.page.title:
                    continue
                title, url = file.page.title, file.page.url
            else:
                title, url = file.name, file.url

            mtime = os.path.getmtime(file.abs_src_path)
            temp_results.append((mtime, rel_path, title, url))

    # 按修改时间倒序
    temp_results.sort(key=lambda x: x[0], reverse=True)
    results = [
        (datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"), *rest)
        for mtime, *rest in temp_results
    ]
    return results[:limit]

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
