import logging
import subprocess
from pathlib import Path
from .utils import read_jsonl_cache, write_jsonl_cache, get_file_creation_time, get_git_first_commit_time

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

def find_mkdocs_projects():
    projects = []
    try:
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            encoding='utf-8'
        ).strip())

        # 遍历 git_root 及子目录, 寻找 mkdocs.yml 文件
        for config_file in git_root.rglob('mkdocs.y*ml'):
            if config_file.name.lower() in ('mkdocs.yml', 'mkdocs.yaml'):
                projects.append(config_file.parent)

        if not projects:
            logger.warning("No MkDocs projects found in the repository")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to find the Git repository root: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while searching for MkDocs projects: {e}")
    
    return projects

def setup_gitattributes(docs_dir: Path):
    try:
        gitattributes_path = docs_dir / '.gitattributes'
        union_merge_line = ".dates_cache.jsonl merge=union"
        # custom_merge_line = ".dates_cache.json merge=custom_json_merge"
        content = gitattributes_path.read_text(encoding='utf-8') if gitattributes_path.exists() else ""
        if union_merge_line not in content:
            if content and not content.endswith('\n'):
                content += '\n'
            content += f"{union_merge_line}\n"
            gitattributes_path.write_text(content, encoding='utf-8')
            subprocess.run(["git", "add", str(gitattributes_path)], check=True)
            logger.info(f"Updated .gitattributes file: {gitattributes_path}")
            return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to read/write .gitattributes file: {e}")
    except Exception as e:
        logger.error(f"Failed to add .gitattributes to git: {e}")
    return False

def update_cache():
    global_updated = False

    for project_dir in find_mkdocs_projects():
        try:
            project_updated = False

            docs_dir = project_dir / 'docs'
            if not docs_dir.exists():
                logger.warning(f"Document directory does not exist: {docs_dir}")
                continue

            # 设置.gitattributes文件
            global_updated = setup_gitattributes(docs_dir)

            # 获取docs目录下已跟踪(tracked)的markdown文件
            cmd = ["git", "ls-files", "*.md"]
            result = subprocess.run(cmd, cwd=docs_dir, capture_output=True, encoding='utf-8')
            tracked_files = result.stdout.splitlines() if result.stdout else []

            if not tracked_files:
                logger.info(f"No tracked markdown files found in {docs_dir}")
                continue

            # 读取 JSONL 缓存
            jsonl_cache_file = docs_dir / '.dates_cache.jsonl'
            jsonl_dates_cache = read_jsonl_cache(jsonl_cache_file)

            # 根据 git已跟踪的文件来更新
            for rel_path in tracked_files:
                try:
                    # 如果文件已在 JSONL 缓存中，跳过
                    if rel_path in jsonl_dates_cache:
                        continue

                    full_path = docs_dir / rel_path
                    if full_path.exists():
                        created_time = get_file_creation_time(full_path).astimezone()
                        if not jsonl_cache_file.exists():
                            git_time = get_git_first_commit_time(full_path)
                            if git_time:
                                created_time = min(created_time, git_time)
                        jsonl_dates_cache[rel_path] = {
                            "created": created_time.isoformat()
                        }
                        project_updated = True
                except Exception as e:
                    logger.error(f"Error processing file {rel_path}: {e}")
                    continue

            # 标记删除不再跟踪的文件
            if len(jsonl_dates_cache) > len(tracked_files):
                project_updated = True

            # 如果有更新，写入 JSONL 缓存文件
            if project_updated or not jsonl_cache_file.exists():
                global_updated = write_jsonl_cache(jsonl_cache_file, jsonl_dates_cache, tracked_files)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute git command: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing project directory {project_dir}: {e}")
            continue
    return global_updated


if __name__ == "__main__":
    update_cache()