import os
import platform
import json
import heapq
import logging
import subprocess
import fnmatch
import re
import math
from pathlib import Path
from operator import itemgetter
from datetime import datetime, timezone
from collections import defaultdict
from mkdocs.structure.files import Files

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


def load_dates_and_authors(docs_dir_path: Path, files: Files):

    # git 创建日期
    created_data = load_git_metadata(docs_dir_path)

    # 覆盖 jsonl 创建日期
    jsonl_cache_file = docs_dir_path / '.dates_cache.jsonl'
    if jsonl_cache_file.exists():
        jsonl_cache = read_jsonl_cache(jsonl_cache_file)
        for filename, new_info in jsonl_cache.items():
            if filename in created_data:
                created_data[filename].update(new_info)

    # git 更新日期
    updated_data = load_git_last_updated_dates(docs_dir_path)

    for file in files:
        if file.inclusion.is_excluded():
            continue
        if not file.src_path.endswith('.md'):
            continue
        rel_path = getattr(file, 'src_uri')

        # created: timestamp -> datetime
        cache = created_data.setdefault(rel_path, {})
        created_ts = cache.get('created')
        cache['created'] = (
            datetime.fromtimestamp(created_ts, tz=timezone.utc)
            if created_ts is not None
            else load_file_creation_date(file.abs_src_path)
        )

        # updated: timestamp -> datetime
        mtime = updated_data.get(rel_path, os.path.getmtime(file.abs_src_path))
        created_data[rel_path]['updated'] = datetime.fromtimestamp(mtime, tz=timezone.utc)

    return created_data

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

def load_file_creation_date(file_path) -> datetime:
    try:
        stat = os.stat(file_path)
        system = platform.system().lower()
        if system.startswith('win'):  # Windows
            return datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        elif system == 'darwin':  # macOS
            try:
                return datetime.fromtimestamp(stat.st_birthtime, tz=timezone.utc)
            except AttributeError:
                return datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        else:  # Linux, 没有创建时间，使用修改时间
            return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    except (OSError, ValueError) as e:
        logger.error(f"Failed to load file creation date for {file_path}: {e}")
        return datetime.now(timezone.utc)

def load_git_first_commit_date(file_path) -> datetime:
    try:
        # git log --reverse --format="%aI" -- {file_path} | head -n 1
        cmd_list = ['git', 'log', '--reverse', '--format=%at', '--', file_path]
        process = subprocess.run(cmd_list, capture_output=True, encoding='utf-8')
        if process.returncode == 0 and process.stdout.strip():
            first_line = int(process.stdout.partition('\n')[0].strip())
            return datetime.fromtimestamp(first_line, tz=timezone.utc)
    except Exception as e:
        logger.info(f"Error load git first commit date for {file_path}: {e}")
    return datetime.now(timezone.utc)

COAUTHOR_RE = re.compile(
    r'^Co-authored-by:\s*(.+?) <([^<>]+)>$',
    re.MULTILINE | re.IGNORECASE
)
def parse_commit_authors(name, email, body):
    authors = [(name, email)]
    seen = {(name, email)}

    for co_name, co_email in COAUTHOR_RE.findall(body):
        author = (co_name, co_email)
        if author in seen:
            continue

        seen.add(author)
        authors.append(author)

    return authors

def load_git_metadata(docs_dir_path: Path):
    dates_cache = {}
    try:
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=docs_dir_path, encoding='utf-8'
        ).strip())
        rel_docs_path = docs_dir_path.relative_to(git_root).as_posix()

        cmd = [
            'git',
            '-c', 'core.quotepath=false',
            'log',
            '--reverse',
            '--no-merges',
            '--use-mailmap',
            '--name-only',
            '-z',
            '--format=%aN%x1f%aE%x1f%at%x1f%B%x00',
            f'--relative={rel_docs_path}',
            '--',
            '*.md'
        ]
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, encoding='utf-8')
        if process.returncode == 0:
            authors_dict = defaultdict(dict)
            first_commit = {}
            current_commit = None

            records = process.stdout.split('\x00')
            for item in records:
                item = item.strip()
                if not item:
                    continue

                parts = item.split('\x1f', 3)
                if len(parts) == 4:
                    name, email, created, body = parts
                    authors = parse_commit_authors(name, email, body)
                    current_commit = (authors, int(created))
                elif item.endswith('.md') and current_commit:
                    authors, created = current_commit
                    # 使用 defaultdict(dict)结构，处理有序与去重
                        # a.巧用 Python 字典的 setdefault 特性来去重（setdefault 为不存在的键提供初始值，不会覆盖已有值）
                        # b.巧用 Python 字典的插入顺序特性来保留内容插入顺序（Python 3.7+ 字典会保持插入顺序）
                    for author in authors:
                        authors_dict[item].setdefault(author, None)

                    first_commit.setdefault(item, created)

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

def load_git_last_updated_dates(docs_dir_path: Path):
    doc_mtime_map = {}
    try:
        git_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=docs_dir_path, encoding='utf-8'
        ).strip())
        rel_docs_path = docs_dir_path.relative_to(git_root).as_posix()

        cmd = ['git', '-c', 'core.quotepath=false', 'log', '--no-merges', '--use-mailmap', '--format=%aN|%aE|%at', '--name-only', f'--relative={rel_docs_path}', '--', '*.md']
        process = subprocess.run(cmd, cwd=docs_dir_path, capture_output=True, encoding='utf-8')
        if process.returncode == 0:
            result = subprocess.run(
                ['git', '-c', 'core.quotepath=false', 'ls-files', '*.md'],
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
                    ts = int(line.split('|')[2])
                elif line.endswith('.md') and line in tracked_files and ts:
                    # 只记录第一次出现的文件，即最近一次提交（setdefault 机制不会覆盖已有值）
                    doc_mtime_map.setdefault(line, ts)
    except Exception as e:
        logger.info(f"Error getting git tracked files in {docs_dir_path}: {e}")

    return doc_mtime_map

# 建议在 on_page_markdown 之后的全局事件中调用，因为需要读取 page.meta 中的信息
def get_recently_updated_files(existing_dates: dict, files: Files, exclude_list: list, limit: int = 10, recent_enable: bool = False, prefix: str = ""):
    recently_updated_results = []
    if recent_enable:
        files_meta = []
        for file in files:
            if file.inclusion.is_excluded():
                continue
            if not file.src_path.endswith('.md'):
                continue
            rel_path = getattr(file, 'src_uri')
            if is_excluded(rel_path, exclude_list):
                continue

            # 优先从现有数据获取 mtime，如果不存在则 fallback 到文件系统 mtime
            exist_updated: datetime = existing_dates.get(rel_path, {}).get('updated')
            mtime = exist_updated.timestamp() if exist_updated else os.path.getmtime(file.abs_src_path)

            # 获取文档其它信息
            title = file.page.title if file.page and file.page.title else file.name
            url = prefix + (file.page.url if file.page and file.page.url else file.url)
            tags = (file.page.meta.get("tags") or []) if file.page else []

            cover = ''
            summary = ''
            readtime = 0
            # authors = []
            if file.page:
                cover = file.page.meta.get('cover', '')
                if cover and not cover.startswith(('http', 'ftp')):
                    cover = prefix + cover.lstrip('/')
                # authors = file.page.meta.document_dates.authors
                if file.page.file:
                    summary, readtime = analyze_markdown(file.page.file.content_string)

            meta_readtime = int((file.page.meta.get('readtime') or 0) if file.page else 0)
            readtime = meta_readtime if meta_readtime > 0 else readtime

            # 存储信息（更新时间、路径、标题、URL、封面、摘要、阅读时间、标签）
            files_meta.append({
                "updated_ts": mtime,
                "rel_path": rel_path,
                "title": title,
                "url": url,
                "cover": cover,
                "summary": summary,
                "readtime": readtime,
                "tags": tags,
            })

        # 构建最近更新列表
        if files_meta:
            # heapq 取 top limit
            recently_updated_results = heapq.nlargest(limit, files_meta, key=itemgetter("updated_ts"))

            for doc in recently_updated_results:
                # timestamp -> utc datetime -> local datetime
                dt = datetime.fromtimestamp(doc["updated_ts"], tz=timezone.utc).astimezone()
                doc["updated_dt"] = dt.isoformat()
                doc["updated"] = dt.date().isoformat()

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
                            if isinstance(file_info, dict):
                                created = file_info.get('created')
                                if isinstance(created, str):
                                    file_info['created'] = int(datetime.fromisoformat(created).timestamp())
                                elif isinstance(created, (int, float)):
                                    file_info['created'] = int(created)
                                dates_cache[file_path] = file_info
                    except (json.JSONDecodeError, StopIteration, ValueError, TypeError,) as e:
                        logger.warning(f"Skipping invalid JSONL line: {e}")
        except OSError as e:
            logger.warning(f"Error reading from '.dates_cache.jsonl': {str(e)}")
    return dates_cache

def write_jsonl_cache(jsonl_file: Path, dates_cache, tracked_files):
    try:
        # 使用临时文件写入，然后替换原文件，避免写入过程中的问题
        temp_file = jsonl_file.with_suffix('.jsonl.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            for file_path in tracked_files:
                if file_path in dates_cache:
                    file_info = dates_cache[file_path].copy()
                    created = file_info.get('created')
                    if created is not None:
                        file_info['created'] = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                    entry = {file_path: file_info}
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # 替换原文件
        temp_file.replace(jsonl_file)
        
        # 将文件添加到git
        subprocess.run(["git", "add", str(jsonl_file)], check=True)
        logger.info(f"Successfully updated JSONL cache file: {jsonl_file}")
        return True
    except OSError as e:
        logger.warning(f"Failed to write JSONL cache file {jsonl_file}: {e}")
    except Exception as e:
        logger.warning(f"Failed to add JSONL cache file to git: {e}")
    return False


# ==================================================
# High-performance Readtime & Summary parser design:
# 
# - O(n) single-pass parser (scan once)
# - No AST construction
# - Finite state machine
# - Block detection: frontmatter / fence / HTML / math / comment
# - Inline and block parsing separated
# - Summary and read-time computed in the same pass
#
# Language support:
# 
# - CJK languages: Chinese, Japanese, Korean
# - Space-delimited languages: English, Spanish, French, German, Portuguese, Russian ...
# - Supports mixed-language content (e.g. English + CJK)
# ==================================================

# ===== Extract Readtime =====
DEFAULT_WPM = 240

# Match Unicode "words" for space-delimited languages (English, Spanish, French, German, Russian, etc.)
# CJK characters also match \w in Python, so they are removed before applying this regex to avoid double counting
WORD_RE = re.compile(r"\w+", re.UNICODE)
# WORD_RE = re.compile(r"[A-Za-z0-9_']+")

# Match common CJK characters (Chinese, Japanese, Korean).
# These languages do not use spaces between words, so characters are counted separately and weighted differently in Readtime
# Ranges:
#   \u4E00–\u9FFF  : Chinese (both Simplified and Traditional)
#   \u3040–\u30FF  : Japanese Hiragana and Katakana
#   \uAC00–\uD7AF  : Korean Hangul syllables
CJK_RE = re.compile(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]")


# ===== Extract Summary =====
# 
# -------- block skip --------
FENCE_RE = re.compile(r"^\s*([`~]{3,})")

# HTML
HTML_TAG_OPEN = re.compile(r"<\s*([a-zA-Z][\w\-]*)\b", re.I)
HTML_VALID_TAGS = {
    "html","head","title","base","link","meta","style",
    "body","article","section","nav","aside","header","footer","main",
    "h1","h2","h3","h4","h5","h6",
    "p","hr","pre","blockquote","ol","ul","li","dl","dt","dd",
    "figure","figcaption","div",
    "a","em","strong","small","s","cite","q","dfn","abbr","data","time",
    "code","var","samp","kbd","sub","sup","i","b","u","mark",
    "ruby","rt","rp","bdi","bdo","span","br","wbr",
    "ins","del",
    "picture","source","img","iframe","embed","object","param",
    "video","audio","track","map","area",
    "svg","math",
    "table","caption","colgroup","col","tbody","thead","tfoot",
    "tr","td","th",
    "form","label","input","button","select","datalist","optgroup",
    "option","textarea","output","progress","meter",
    "fieldset","legend",
    "details","summary","dialog",
    "script","noscript","template","slot","canvas",
    "font","center","big","tt","strike","basefont","dir","applet"
}
HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr",
    "img", "input", "link", "meta", "param",
    "source", "track", "wbr"
}

# -------- inline skip --------
# TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
REF_LINK_RE = re.compile(r"^\s*\[.+?\]:")
H1_TITLE = re.compile(r"^\s*# .+$", re.MULTILINE)
SINGLE_LINE_HTML_NOISE = re.compile(r"^</?[a-z][\w-]*[^>]*>", re.I)
def inline_skip(line: str):
    s = line.lstrip()
    if s.startswith(">"):
        return True
    if s.startswith("!!!") or s.startswith("???"):
        return True
    if s.startswith("==="):
        return True
    return False

# -------- inline replace --------
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BRACE_RE = re.compile(r"\{[^}]*\}")
MD_SYNTAX_RE = re.compile(r"[`*_#]+")


def analyze_markdown(md: str) -> list:
    # ---------- for Readtime ----------
    words = 0
    cjk = 0
    images = 0
    table_rows = 0
    code_rows = 0
    math_blocks = 0

    # ---------- for Summary ----------
    summary_lines = []

    state = "NORMAL"
    fence = ""
    html_close_re = None
    frontmatter_parsed = False
    h1_parsed = False
    math_delim = ""

    for line in md.splitlines():
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
            else:
                frontmatter_parsed = True

        # ==================================================
        # 2. Fence Block
        # ==================================================
        if state == "FENCE":
            if stripped.startswith(fence):
                state = "NORMAL"
            else:
                code_rows += 1
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
            if stripped.endswith("-->"):
                state = "NORMAL"
            continue

        if state == "NORMAL" and stripped.startswith("<!--"):
            state = "COMMENT"
            if stripped.endswith("-->"):
                state = "NORMAL"
            continue

        # ==================================================
        # 4. HTML Block
        # ==================================================
        # Counting img tags in html
        lower = stripped.lower()
        if "<img " in lower:
            images += lower.count("<img ")

        if state == "HTML_BLOCK":
            if html_close_re and html_close_re in lower:
                state = "NORMAL"
                html_close_re = None
            continue

        if state == "NORMAL":
            if stripped.startswith("<"):
                m = HTML_TAG_OPEN.match(stripped)
                if m:
                    tag = m.group(1).lower()

                    # Normal tags: required </tag>
                    if tag in HTML_VALID_TAGS and tag not in HTML_VOID_TAGS:
                        html_close_re = f"</{tag}>"
                        if html_close_re in lower:
                            continue
                    else:
                        # VOID or Non-standard tags: as long as they end in >
                        html_close_re = ">"
                        if stripped.endswith(html_close_re):
                            continue

                    # Going here means that the multiline HTML block
                    state = "HTML_BLOCK"
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
            math_blocks += 1
            continue

        # ==================================================
        # 6. Inline Skip
        # ==================================================
        if state == "NORMAL":
            if stripped.startswith("|") and stripped.endswith("|"):
            # if TABLE_ROW_RE.match(stripped):
                table_rows += 1
                continue
            if inline_skip(stripped):
                continue
            if REF_LINK_RE.match(stripped):
                continue
            if not h1_parsed:
                if H1_TITLE.match(stripped):
                    h1_parsed = True
                    continue
            if stripped.startswith(("---", "***", "___")):
                continue
            if SINGLE_LINE_HTML_NOISE.match(stripped):
                continue

        # ==================================================
        # 7. Inline Replace
        # ==================================================
        if "![" in stripped:
            images += len(IMAGE_RE.findall(stripped))

        text = stripped
        text = IMAGE_RE.sub("", text)
        text = LINK_RE.sub(r"\1", text)
        text = BRACE_RE.sub("", text)

        text = text.strip()
        if text:
            cjk += len(CJK_RE.findall(text))
            # CJK characters also match \w, so remove them before applying \w to avoid double counting!
            text_no_cjk = CJK_RE.sub(" ", text)
            words += len(WORD_RE.findall(text_no_cjk))

            # Make the summary break early
            if len(summary_lines) < 10:
                summary_lines.append(text)

    # ===============================
    # compute read time
    # ===============================
    units = words + cjk / 2
    seconds = math.ceil(units / DEFAULT_WPM * 60)

    seconds += table_rows * 2
    seconds += code_rows
    seconds += math_blocks * 4
    seconds += images * 2

    summary = MD_SYNTAX_RE.sub("", "  ".join(summary_lines)).strip()
    minutes = max(1, math.ceil(seconds / 60))

    return summary, minutes
