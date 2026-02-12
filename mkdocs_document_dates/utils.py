import os
import platform
import json
import heapq
import logging
import subprocess
import fnmatch
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from mkdocs.structure.files import Files

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


def compile_exclude_patterns(exclude_list):
    if not exclude_list:
        return []
    return [re.compile(fnmatch.translate(pattern)) for pattern in exclude_list]

def is_excluded(path, patterns):
    if not patterns:
        return False
    first = patterns[0]
    if isinstance(first, re.Pattern):
        for regex in patterns:
            if regex.match(path):
                return True
    else:
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
    return False

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

def load_git_metadata(docs_dir_path: Path):
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

def load_git_last_updated_date(docs_dir_path: Path):
    doc_mtime_map = {}
    try:
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
            # 只记录已跟踪的文件（还有已删除、重命名、不再跟踪）
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

    return doc_mtime_map

# 建议在 on_page_markdown 之后的全局事件中调用，因为需要读取 page.meta 中的信息
def get_recently_updated_files(existing_dates: dict, files: Files, exclude_list: list, limit: int = 10, recent_enable: bool = False):
    recently_updated_results = []
    if recent_enable:
        files_meta = []
        for file in files:
            if file.inclusion.is_excluded():
                continue
            if not file.src_path.endswith('.md'):
                continue
            rel_path = getattr(file, 'src_uri', file.src_path)
            if os.sep != '/':
                rel_path = rel_path.replace(os.sep, '/')
            if is_excluded(rel_path, exclude_list):
                continue

            # 优先从现有数据获取 mtime，如果不存在则 fallback 到文件系统 mtime
            mtime = existing_dates.get(rel_path, os.path.getmtime(file.abs_src_path))

            # 获取文档标题和 URL
            title = file.page.title if file.page and file.page.title else file.name
            url = file.page.url if file.page and file.page.url else file.url

            cover = ''
            summary = ''
            # authors = []
            if file.page:
                cover = file.page.meta.get('cover', '')
                # authors = file.page.meta.get('document_dates_authors', [])
                if file.page.file:
                    summary = extract_summary(file.page.file.content_string)

            # 存储信息
            files_meta.append((mtime, rel_path, title, url, cover, summary))
            # existing_map[rel_path] = mtime

        # 构建最近更新列表
        if files_meta:
            # heapq 取 top limit
            top_results = heapq.nlargest(limit, files_meta, key=lambda x: x[0])
            recently_updated_results = [
                (datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"), *rest)
                for mtime, *rest in top_results
            ]

    return recently_updated_results

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


# ===== Extract Summary =====
# 
# -------- block skip --------
# Fence
FENCE_RE = re.compile(r"^\s*([`~]{3,})")

# HTML comment
HTML_COMMENT_START = re.compile(r'<!--', re.I)
HTML_COMMENT_END   = re.compile(r'-->', re.I)

# HTML
HTML_TAG_OPEN = re.compile(r'<\s*([a-zA-Z][\w\-]*)\b', re.I)
HTML_TAG_CLOSE_TEMPLATE = r"</\s*{}\s*>"
HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr",
    "img", "input", "link", "meta", "param",
    "source", "track", "wbr"
}
HTML_VOID_CLOSE_RE = re.compile(r">", re.I)

# -------- inline skip --------
H1_TITLE = re.compile(r'^\s*# .+$', re.MULTILINE)
SINGLE_LINE_HTML_NOISE = re.compile(r'^</?[a-z][\w-]*[^>]*>$', re.I)
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
INLINE_SKIP_RE = re.compile(
    r"""
    ^\s*> |                 # quote
    ^\s*(?:!!!|\?\?\?) |    # admonition
    ^\s*=== |               # tab
    ^\s*\[.+?\]:            # reference link, including footnote
    """,
    re.X,
)

# -------- inline replace --------
IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')
LINK_RE = re.compile(r'\[([^\]]+)\]\([^)]+\)')
BRACE_RE = re.compile(r"\{[^}]*\}")
MD_SYNTAX_RE = re.compile(r'[`*_>#]+')

def clean_markdown(md: str) -> list:

    lines = md.splitlines()
    result = []

    state = "NORMAL"
    fence = ""
    html_close_re = None
    frontmatter_parsed = False
    h1_parsed = False
    math_delim = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # ==================================================
        # 1. Frontmatter
        # ==================================================
        if not frontmatter_parsed:
            if state == "FRONTMATTER":
                if stripped in ("---", "+++"):
                    state = "NORMAL"
                    frontmatter_parsed = True
                continue
            
            if state == "NORMAL" and stripped in ("---", "+++"):
                state = "FRONTMATTER"
                continue

        # ==================================================
        # 2. Fence Block
        # ==================================================
        if state == "FENCE":
            if stripped.startswith(fence):
                state = "NORMAL"
            continue
 
        if state == "NORMAL":
            m = FENCE_RE.match(stripped)
            if m:
                fence = m.group(1)
                state = "FENCE"
                continue

        # ==================================================
        # 3. HTML Comment
        # ==================================================
        if state == "COMMENT":
            if HTML_COMMENT_END.search(stripped):
                state = "NORMAL"
            continue

        if state == "NORMAL" and HTML_COMMENT_START.search(stripped):
            state = "COMMENT"
            if HTML_COMMENT_END.search(stripped):
                state = "NORMAL"
            continue

        # ==================================================
        # 4. HTML Block
        # ==================================================
        if state == "HTML_BLOCK":
            if html_close_re and html_close_re.search(stripped):
                state = "NORMAL"
                html_close_re = None
            continue

        if state == "NORMAL":
            m = HTML_TAG_OPEN.match(stripped)
            if m:
                tag = m.group(1).lower()
                is_void = tag in HTML_VOID_TAGS

                # void tag：单行且以 > 结尾，视为直接结束，忽略该行
                if stripped.endswith('>') and is_void:
                    continue

                # 非 void tag：进入 HTML_BLOCK
                state = "HTML_BLOCK"
                if is_void:
                    html_close_re = HTML_VOID_CLOSE_RE
                else:
                    html_close_re = re.compile(HTML_TAG_CLOSE_TEMPLATE.format(re.escape(tag)), re.I)

                # same-line close: <div>...</div>
                if html_close_re.search(stripped):
                    state = "NORMAL"
                    html_close_re = None

                continue

        # ==================================================
        # 5. Math Block
        # ==================================================
        if state == "MATH":
            if stripped == math_delim:
                state = "NORMAL"
            continue

        if state == "NORMAL" and stripped in ("$$", "\\["):
            math_delim = "$$" if stripped == "$$" else "\\]"
            state = "MATH"
            continue

        # ==================================================
        # 6. Inline Skip
        # ==================================================
        if state == "NORMAL":
            if TABLE_ROW_RE.match(stripped):
                continue
            if INLINE_SKIP_RE.match(stripped):
                continue
            # 单行 HTML 噪音兜底
            if SINGLE_LINE_HTML_NOISE.match(stripped):
                continue
            if not h1_parsed:
                if H1_TITLE.match(stripped):
                    h1_parsed = True
                    continue
            if stripped.startswith(('---', '***')):
                continue

        # ==================================================
        # 7. Inline Replace
        # ==================================================
        text = stripped
        text = IMAGE_RE.sub("", text)
        text = LINK_RE.sub(r"\1", text)
        text = BRACE_RE.sub("", text)

        text = text.strip()
        if text:
            result.append(text)

            # 提前熔断
            if len(result) >= 10:
                break

        # 锁定 Frontmatter 状态，防止后续 --- 干扰
        frontmatter_parsed = True

    return result
    # return "\n".join(result)

def extract_summary(markdown_text: str) -> str:
    md_list = clean_markdown(markdown_text)
    text = "  ".join(md_list)
    return MD_SYNTAX_RE.sub('', text).strip()