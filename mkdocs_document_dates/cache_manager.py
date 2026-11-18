import logging
import yaml
import os
import subprocess
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from .utils import read_jsonl_cache, write_jsonl_cache, load_file_creation_date, load_git_first_commit_date

logger = logging.getLogger("mkdocs.plugins.document_dates")
_LOGGING_CONFIGURED = False

CONFIG_PRIORITY = {
    "mkdocs.yml": 0,
    "properdocs.yml": 1,
    "mkdocs.yaml": 2,
    "properdocs.yaml": 3,
}

def _default_log_file() -> Path:
    try:
        git_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            env=_clean_git_env(),
            encoding="utf-8"
        ).strip())
        base_dir = git_root
    except Exception:
        base_dir = Path.cwd()
    return base_dir / "mkdocs_document_dates.log"

def configure_file_logging(log_file: Optional[Path] = None, level: int = logging.DEBUG) -> Optional[Path]:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return log_file

    env_log_file = os.getenv("MKDOCS_DOCUMENT_DATES_LOG_FILE")
    if log_file is None and env_log_file:
        log_file = Path(env_log_file).expanduser()

    if log_file is None:
        return None

    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    _LOGGING_CONFIGURED = True
    logger.debug(f"File logging enabled: {log_file}")
    return log_file

def _env_truthy(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return False
    value = value.strip().lower()
    return value not in ("", "0", "false", "no", "off")


def _clean_git_env():
    env = os.environ.copy()

    for k in [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_SUPER_PREFIX",
        "GIT_CEILING_DIRECTORIES",
    ]:
        env.pop(k, None)

    env["GIT_OPTIONAL_LOCKS"] = "0"

    return env

def find_mkdocs_projects():
    projects = {}

    try:
        git_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            env=_clean_git_env(),
            encoding="utf-8"
        ).strip())

        for pattern in ("*.yml", "*.yaml"):
            for config_file in git_root.rglob(pattern):
                name = config_file.name.lower()
                if name not in CONFIG_PRIORITY:
                    continue

                project_dir = config_file.parent
                existing = projects.get(project_dir)
                if existing is None:
                    projects[project_dir] = config_file
                    continue
                if CONFIG_PRIORITY[name] < CONFIG_PRIORITY[existing.name.lower()]:
                    projects[project_dir] = config_file

        if not projects:
            logger.warning("No MkDocs/ProperDocs projects found in the repository")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to find the Git repository root: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while searching for projects: {e}")

    return projects

def get_renamed_files(docs_dir: Path) -> dict:
    """获取本次提交中被重命名/移动的 markdown 文件，返回 {旧路径: 新路径}

    路径均相对 docs_dir，与 JSONL 缓存的 key 格式一致。
    在 pre-commit 阶段对比 HEAD 与暂存区，依靠 git 的 -M 相似度检测识别移动，
    因此 `git mv` 和「手动 mv + git add」两种方式都能覆盖。

    这里刻意以仓库根为视角（--no-relative）再自行过滤，只保留两端都在 docs_dir
    内的重命名。若改用 --relative，git 只能看见 docs_dir 内部的增删，会把
    「移出去的文件」和「移进来的相似文件」误配成一次重命名，导致创建日期张冠李戴。
    """
    renames = {}
    try:
        git_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=docs_dir, env=_clean_git_env(), encoding="utf-8"
        ).strip()).resolve()
        rel_docs = docs_dir.resolve().relative_to(git_root)
        # docs_dir 就是仓库根时前缀为空，否则形如 "docs/"
        prefix = "" if rel_docs == Path(".") else rel_docs.as_posix() + "/"

        # --no-relative 抵消用户可能配置的 diff.relative=true
        cmd = [
            "git", "-c", "core.quotepath=false",
            "diff", "--cached", "-M", "--name-status", "-z", "--no-relative",
        ]
        result = subprocess.run(cmd, cwd=docs_dir, env=_clean_git_env(),
                                capture_output=True, encoding="utf-8")
        if result.returncode != 0 or not result.stdout:
            return renames

        # -z 输出格式: 重命名为 "R<score>\0旧路径\0新路径"，其余为 "<status>\0路径"
        fields = result.stdout.split("\0")
        i = 0
        while i < len(fields):
            status = fields[i]
            if not status:
                i += 1
                continue
            # R(重命名) 和 C(复制) 均为三字段，但只有 R 需要迁移
            if status[0] in ("R", "C"):
                if i + 2 < len(fields):
                    old_path, new_path = fields[i + 1], fields[i + 2]
                    # 只保留两端都在 docs_dir 内的 markdown 重命名，
                    # 跨 docs_dir 边界的移动没有可继承的创建日期
                    if (status[0] == "R"
                            and old_path.endswith(".md") and new_path.endswith(".md")
                            and old_path.startswith(prefix) and new_path.startswith(prefix)):
                        renames[old_path[len(prefix):]] = new_path[len(prefix):]
                i += 3
            else:
                i += 2
    except Exception as e:
        logger.warning(f"Failed to detect renamed files in {docs_dir}: {e}")
    return renames

def migrate_renamed_entries(dates_cache: dict, docs_dir: Path) -> bool:
    """把被重命名文件的创建日期从旧路径迁移到新路径

    不这样做的话，新路径不在缓存中，会被当作新文件重新取创建时间
    （Linux 上即文件的 mtime，也就是重命名的那一刻），原始创建日期就丢了。
    """
    renames = get_renamed_files(docs_dir)
    if not renames:
        return False

    # 分两阶段：先全部摘出，再统一落位。
    # 这样 a→b 与 b→a 这类互换也能正确处理（单阶段时会因目标已存在而互相阻塞）
    pending = {}
    for old_path, new_path in renames.items():
        if old_path in dates_cache:
            pending[new_path] = (old_path, dates_cache.pop(old_path))

    migrated = False
    for new_path, (old_path, info) in pending.items():
        # 目标已被别的条目占用时不覆盖（重命名恰好盖掉一个已存在的文件）
        if new_path in dates_cache:
            logger.info(f"Skipped migration, target already exists: {old_path} -> {new_path}")
            continue
        dates_cache[new_path] = info
        migrated = True
        logger.info(f"Migrated created date: {old_path} -> {new_path}")
    return migrated

def setup_gitattributes(docs_dir: Path):
    try:
        gitattributes_path = docs_dir / ".gitattributes"
        union_merge_line = ".dates_cache.jsonl merge=union"
        # custom_merge_line = ".dates_cache.json merge=custom_json_merge"
        content = gitattributes_path.read_text(encoding="utf-8") if gitattributes_path.exists() else ""
        if union_merge_line not in content:
            if content and not content.endswith("\n"):
                content += "\n"
            content += f"{union_merge_line}\n"
            gitattributes_path.write_text(content, encoding="utf-8")
            subprocess.run(["git", "add", str(gitattributes_path)], cwd=docs_dir, env=_clean_git_env(), check=True)
            logger.info(f"Updated .gitattributes file: {gitattributes_path}")
            return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to read/write .gitattributes file: {e}")
    except Exception as e:
        logger.error(f"Failed to add .gitattributes to git: {e}")
    return False

def update_cache():
    if os.getenv("MKDOCS_DOCUMENT_DATES_LOG_FILE"):
        configure_file_logging()
    elif _env_truthy("MKDOCS_DOCUMENT_DATES_DEBUG"):
        configure_file_logging(_default_log_file())

    global_updated = False
    for project_dir, mkdocs_yml in find_mkdocs_projects().items():
        try:
            project_updated = False

            docs_dir = project_dir / "docs"

            # 从 mkdocs.yml 中读取 docs_dir 配置覆盖默认值
            try:
                mkdocs_config = yaml.load(
                    mkdocs_yml.read_text(encoding="utf-8"),
                    Loader=yaml.BaseLoader,
                ) or {}

                docs_dir_name = mkdocs_config.get("docs_dir") or "docs"
                docs_dir = (project_dir / docs_dir_name).resolve(strict=False)
            except (IOError, OSError, yaml.YAMLError) as e:
                logger.warning(f"Failed to read docs_dir: {e}")

            if not docs_dir.is_dir():
                logger.info(f"Document directory does not exist: {docs_dir}")
                continue

            # 设置.gitattributes文件
            global_updated |= setup_gitattributes(docs_dir)

            # 获取docs目录下已跟踪(tracked)的markdown文件
            cmd = ["git", "-c", "core.quotepath=false", "ls-files", "*.md"]
            result = subprocess.run(cmd, cwd=docs_dir, env=_clean_git_env(), capture_output=True, encoding="utf-8")
            tracked_files = result.stdout.splitlines() if result.stdout else []

            if not tracked_files:
                logger.info(f"No tracked markdown files found in {docs_dir}")
                continue

            # 读取 JSONL 缓存
            jsonl_cache_file = docs_dir / ".dates_cache.jsonl"
            jsonl_dates_cache = read_jsonl_cache(jsonl_cache_file)

            # 迁移重命名/移动文件的创建日期（须在下面的循环之前，否则会被当作新文件处理）
            if jsonl_dates_cache:
                project_updated |= migrate_renamed_entries(jsonl_dates_cache, docs_dir)

            # 根据 git已跟踪的文件来更新
            for rel_path in tracked_files:
                try:
                    # 如果文件已在 JSONL 缓存中，跳过
                    if rel_path in jsonl_dates_cache:
                        continue

                    full_path = docs_dir / rel_path
                    if full_path.exists():
                        created_time = load_file_creation_date(full_path)
                        if not jsonl_cache_file.exists():
                            git_time = load_git_first_commit_date(full_path)
                            if git_time:
                                created_time = min(created_time, git_time)
                        jsonl_dates_cache[rel_path] = {
                            "created": int(created_time.timestamp())
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
                global_updated |= write_jsonl_cache(jsonl_cache_file, jsonl_dates_cache, tracked_files)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute git command: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing project directory {project_dir}: {e}")
            continue
    return global_updated


if __name__ == "__main__":
    update_cache()
