import os
import json
import logging
import platform
import subprocess
from datetime import datetime
from pathlib import Path

# 配置日志等级 (INFO WARNING ERROR)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

def find_mkdocs_projects():
    projects = []
    try:
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            text=True, encoding='utf-8'
        ).strip())

        # 遍历 git_root 及子目录, 寻找 mkdocs.yml 文件
        for config_file in git_root.rglob('mkdocs.y*ml'):
            if config_file.name.lower() in ('mkdocs.yml', 'mkdocs.yaml'):
                projects.append(config_file.parent)

        if not projects:
            logging.warning("No MkDocs projects found in the repository")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to find the Git repository root: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while searching for MkDocs projects: {e}")
    
    return projects

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
        logging.error(f"Failed to get file creation time for {file_path}: {e}")
        return datetime.now()

def get_git_first_commit_time(file_path):
    try:
        # git log --reverse --format="%aI" --date=iso -- {file_path} | head -n 1
        result = subprocess.run(['git', 'log', '--reverse', '--format=%aI', '--', file_path], capture_output=True, text=True)
        if result.returncode == 0:
            first_line = result.stdout.partition('\n')[0].strip()
            if first_line:
                return datetime.fromisoformat(first_line).replace(tzinfo=None)
    except Exception as e:
        logging.info(f"Error getting git first commit time for {file_path}: {e}")
    return None

def setup_gitattributes(docs_dir):
    updated = False
    try:
        gitattributes_path = docs_dir / '.gitattributes'
        union_config_line = ".dates_cache.jsonl merge=union"
        if gitattributes_path.exists():
            with open(gitattributes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if union_config_line not in content:
                with open(gitattributes_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{union_config_line}\n")
                updated = True
        else:
            with open(gitattributes_path, 'w', encoding='utf-8') as f:
                f.write(f"{union_config_line}\n")
            updated = True
        
        if updated:
            subprocess.run(["git", "add", str(gitattributes_path)], check=True)
            logging.info(f"Updated .gitattributes file: {gitattributes_path}")
    except (IOError, OSError) as e:
        logging.error(f"Failed to read/write .gitattributes file: {e}")
    except Exception as e:
        logging.error(f"Failed to add .gitattributes to git: {e}")
    
    return updated

def read_json_cache(cache_file):
    dates_cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding='utf-8') as f:
                dates_cache = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Error reading from '.dates_cache.json': {str(e)}")
    return dates_cache

def read_jsonl_cache(jsonl_file):
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
                        logging.warning(f"Skipping invalid JSONL line: {e}")
        except IOError as e:
            logging.warning(f"Error reading from '.dates_cache.jsonl': {str(e)}")
    return dates_cache

def write_jsonl_cache(jsonl_file, dates_cache, tracked_files):
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
        logging.info(f"Successfully updated JSONL cache file: {jsonl_file}")
        return True
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to write JSONL cache file {jsonl_file}: {e}")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to add JSONL cache file to git: {e}")
        return False

def update_cache():
    global_updated = False

    for project_dir in find_mkdocs_projects():
        try:
            project_updated = False

            docs_dir = project_dir / 'docs'
            if not docs_dir.exists():
                logging.error(f"Document directory does not exist: {docs_dir}")
                continue

            # 设置.gitattributes文件
            gitattributes_updated = setup_gitattributes(docs_dir)
            if gitattributes_updated:
                global_updated = True

            # 获取docs目录下已跟踪(tracked)的markdown文件
            cmd = ["git", "ls-files", "*.md"]
            result = subprocess.run(cmd, cwd=docs_dir, capture_output=True, text=True, check=True)
            tracked_files = result.stdout.splitlines() if result.stdout else []

            if not tracked_files:
                logging.info(f"No tracked markdown files found in {docs_dir}")
                continue

            # 读取旧的JSON缓存文件（如果存在）
            json_cache_file = docs_dir / '.dates_cache.json'
            json_dates_cache = read_json_cache(json_cache_file)

            # 读取新的JSONL缓存文件（如果存在）
            jsonl_cache_file = docs_dir / '.dates_cache.jsonl'
            jsonl_dates_cache = read_jsonl_cache(jsonl_cache_file)

            # 根据 git已跟踪的文件来更新
            for rel_path in tracked_files:
                try:
                    # 如果文件已在JSONL缓存中，跳过
                    if rel_path in jsonl_dates_cache:
                        continue

                    full_path = docs_dir / rel_path
                    # 处理新文件或迁移旧JSON缓存
                    if rel_path in json_dates_cache:
                        jsonl_dates_cache[rel_path] = json_dates_cache[rel_path]
                        project_updated = True
                    elif full_path.exists():
                        created_time = get_file_creation_time(full_path)
                        if not jsonl_cache_file.exists() and not json_cache_file.exists():
                            git_time = get_git_first_commit_time(full_path)
                            if git_time:
                                created_time = min(created_time, git_time)
                        jsonl_dates_cache[rel_path] = {
                            "created": created_time.isoformat()
                        }
                        project_updated = True
                except Exception as e:
                    logging.error(f"Error processing file {rel_path}: {e}")
                    continue

            # 标记删除不再跟踪的文件
            files_to_remove = set(jsonl_dates_cache.keys()) - set(tracked_files)
            if files_to_remove:
                project_updated = True
                logging.info(f"Removing {len(files_to_remove)} untracked files from cache")

            # 如果有更新，写入JSONL缓存文件
            if project_updated or not jsonl_cache_file.exists():
                if write_jsonl_cache(jsonl_cache_file, jsonl_dates_cache, tracked_files):
                    global_updated = True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to execute git command: {e}")
            continue
        except Exception as e:
            logging.error(f"Error processing project directory {project_dir}: {e}")
            continue

    return global_updated


if __name__ == "__main__":
    update_cache()