import os
import json
import shutil
import platform
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Union, List
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

# 配置日志等级 (INFO WARNING ERROR)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)


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


class DocumentDatesPlugin(BasePlugin):
    config_scheme = (
        ('type', config_options.Type(str, default='date')),
        ('locale', config_options.Type(str, default='en')),
        ('date_format', config_options.Type(str, default='%Y-%m-%d')),
        ('time_format', config_options.Type(str, default='%H:%M:%S')),
        ('position', config_options.Type(str, default='bottom')),
        ('exclude', config_options.Type(list, default=[])),
        ('created_field_names', config_options.Type(list, default=['created', 'date', 'creation'])),
        ('modified_field_names', config_options.Type(list, default=['modified', 'updated', 'last_modified', 'last_updated'])),
        ('show_author', config_options.Type(bool, default=True)),
        ('author_field_mapping', config_options.Type(dict, default={
            'name': ['name', 'author'],
            'email': ['email', 'mail']
        }))
    )

    def __init__(self):
        super().__init__()
        self.translation = {}
        self.dates_cache = {}
        self.is_git_repo = False

    def on_config(self, config):
        
        # 检查是否为 Git 仓库
        try:
            check_git = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
            if check_git.returncode == 0:
                self.is_git_repo = True
        except Exception as e:
            logging.info(f"Not a Git repository: {str(e)}")

        docs_dir_path = Path(config['docs_dir'])

        # 加载 json 语言文件
        self._load_translation(docs_dir_path)

        # 加载日期缓存
        jsonl_cache_file = docs_dir_path / '.dates_cache.jsonl'
        if jsonl_cache_file.exists():
            try:
                with open(jsonl_cache_file, "r", encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry and isinstance(entry, dict) and len(entry) == 1:
                                file_path, file_info = next(iter(entry.items()))
                                self.dates_cache[file_path] = file_info
                        except (json.JSONDecodeError, StopIteration) as e:
                            logging.warning(f"Skipping invalid JSONL line: {e}")
                logging.info(f"Loaded cache from JSONL file: {jsonl_cache_file}")
            except IOError as e:
                logging.warning(f"Error reading from '.dates_cache.jsonl': {str(e)}")
        
        # 兼容旧版缓存文件
        json_cache_file = docs_dir_path / '.dates_cache.json'
        if not self.dates_cache and json_cache_file.exists():
            try:
                with open(json_cache_file, "r", encoding='utf-8') as f:
                    self.dates_cache = json.load(f)
                logging.info(f"Loaded cache from JSON file: {json_cache_file}")
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Error reading from '.dates_cache.json': {str(e)}")        
        
        
        if 'extra_css' not in config:
            config['extra_css'] = []
        if 'extra_javascript' not in config:
            config['extra_javascript'] = []
        
        # 加载图标 Google Fonts Icons: https://fonts.google.com/icons
        material_icons_url = 'https://fonts.googleapis.com/icon?family=Material+Icons'
        if material_icons_url not in config['extra_css']:
            config['extra_css'].append(material_icons_url)
        
        # 加载 Tooltip 资源：Tippy.js
        """
        # core
            https://unpkg.com/@popperjs/core@2/dist/umd/popper.min.js
            https://unpkg.com/tippy.js@6/dist/tippy.umd.min.js
            https://unpkg.com/tippy.js@6/dist/tippy.css
        # animations
            https://unpkg.com/tippy.js@6/animations/scale.css
        # animations: Material filling effect
            https://unpkg.com/tippy.js@6/dist/backdrop.css
            https://unpkg.com/tippy.js@6/animations/shift-away.css
        # themes
            https://unpkg.com/tippy.js@6/themes/light.css
            https://unpkg.com/tippy.js@6/themes/material.css
        """
        # 复制静态资源到用户目录
        dest_dir = docs_dir_path / 'assets/document_dates'
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for dir_name in ['tippy', 'core']:
            source_dir = Path(__file__).parent / 'static' / dir_name
            target_dir = dest_dir / dir_name
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
        
        # 复制配置文件模板到用户目录（如果不存在）
        config_files = ['user.config.css', 'user.config.js']
        for config_file in config_files:
            source_config = Path(__file__).parent / 'static/config' / config_file
            target_config = dest_dir / config_file
            if not target_config.exists():
                shutil.copy2(source_config, target_config)

        # 加载 timeago.js
        # https://cdn.jsdelivr.net/npm/timeago.js@4.0.2/dist/timeago.min.js
        # https://cdnjs.cloudflare.com/ajax/libs/timeago.js/4.0.2/timeago.full.min.js
        if self.config['type'] == 'timeago':
            config['extra_javascript'].insert(0, 'assets/document_dates/core/timeago.min.js')
            config['extra_javascript'].insert(1, 'assets/document_dates/core/timeago-load.js')

        # 加载 Tippy CSS 文件
        tippy_css_dir = dest_dir / 'tippy'
        for css_file in tippy_css_dir.glob('*.css'):
            config['extra_css'].append(f'assets/document_dates/tippy/{css_file.name}')
        
        # 加载自定义 CSS 文件
        config['extra_css'].extend([
            'assets/document_dates/core/core.css',
            'assets/document_dates/user.config.css'
        ])
        
        # 按顺序加载 Tippy JS 文件
        js_core_files = ['popper.min.js', 'tippy.umd.min.js']
        for js_file in js_core_files:
            config['extra_javascript'].append(f'assets/document_dates/tippy/{js_file}')
        
        # 加载自定义 JS 文件
        config['extra_javascript'].extend([
            'assets/document_dates/core/core.js',
            'assets/document_dates/user.config.js'
        ])

        return config

    def on_page_markdown(self, markdown, page, config, files):
        # 获取文件的绝对路径和相对路径
        file_path = page.file.abs_src_path
        rel_path = page.file.src_path
        
        # 检查是否需要排除
        if self._is_excluded(rel_path):
            return markdown
        
        # 获取时间信息，优先从 front matter 获取
        created = self._find_meta_date(page.meta, self.config['created_field_names'])
        modified = self._find_meta_date(page.meta, self.config['modified_field_names'])
        
        if not created:
            created = self._get_file_creation_time(file_path, rel_path)
        if not modified:
            modified = self._get_file_modification_time(file_path)
  
        # 获取作者信息
        author = None
        if self.config['show_author']:
            author = self._process_meta_author(page.meta)
            if not author:
                author = self._get_git_authors(file_path)
                if not author:
                    author = self._get_local_author()
        
        # 生成日期和作者信息 HTML
        info_html = self._generate_html_info(created, modified, author)
        
        # 将信息写入 markdown
        return self._insert_date_info(markdown, info_html)


    def _load_translation(self, docs_dir_path):
        # 内置语言文件目录
        builtin_dir = Path(__file__).parent / 'static' / 'languages'
        # 用户自定义语言文件目录
        custom_dir = docs_dir_path / 'assets' / 'document_dates' / 'languages'

        # 加载语言文件
        self._load_lang_file(builtin_dir)
        self._load_lang_file(custom_dir)
        if not self.translation:
            self.config['locale'] = 'en'
            self._load_lang_file(builtin_dir)

        # 复制 en.json 到用户目录作为自定义参考
        custom_en_json = custom_dir / 'en.json'
        if not custom_en_json.exists():
            custom_dir.mkdir(parents=True, exist_ok=True)
            en_json = builtin_dir / 'en.json'
            shutil.copy2(en_json, custom_en_json)

    def _load_lang_file(self, lang_dir):
        try:
            locale_file = lang_dir / f"{self.config['locale']}.json"
            if locale_file.exists():
                with locale_file.open('r', encoding='utf-8') as f:
                    self.translation = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format in language file {locale_file}: {str(e)}")
        except Exception as e:
            logging.error(f"Error loading language file {locale_file}: {str(e)}")


    def _is_excluded(self, rel_path) -> bool:
        for pattern in self.config['exclude']:
            if self._matches_exclude_pattern(rel_path, pattern):
                return True
        return False

    def _matches_exclude_pattern(self, rel_path, pattern) -> bool:
        try:
            # 情况1：匹配具体文件路径
            if '*' not in pattern:
                return rel_path == pattern

            # 情况2：匹配目录下所有文件（包含子目录）
            if pattern.endswith('/*'):
                return rel_path.startswith(pattern[:-1])

            # 情况3：匹配指定目录下的特定类型文件（不包含子目录）
            if '*.' in pattern:
                pattern_path = Path(pattern)
                rel_path_obj = Path(rel_path)
                pattern_dir = pattern_path.parent
                pattern_suffix = pattern_path.name[1:]  # 去掉 * 号
                return (rel_path_obj.parent == pattern_dir and 
                    rel_path_obj.name.endswith(pattern_suffix))

            return False
        except ValueError:
            return False


    def _find_meta_date(self, meta: dict, field_names: list) -> Union[datetime, None]:
        for field in field_names:
            if field in meta:
                try:
                    # 移除首尾可能存在的单双引号和时区信息
                    date_str = str(meta[field]).strip("'\"")
                    return datetime.fromisoformat(date_str).replace(tzinfo=None)
                except Exception:
                    continue
        return None

    def _get_git_first_commit_time(self, file_path):
        if self.is_git_repo:
            try:
                # git log --reverse --format="%aI" --date=iso -- {file_path} | head -n 1
                result = subprocess.run(['git', 'log', '--reverse', '--format=%aI', '--', file_path], capture_output=True, text=True)
                if result.returncode == 0:
                    commits = result.stdout.strip().split('\n')
                    if commits and commits[0]:
                        return datetime.fromisoformat(commits[0]).replace(tzinfo=None)
            except Exception as e:
                logging.warning(f"Error getting git first commit time for {file_path}: {e}")
        return None

    def _get_file_creation_time(self, file_path, rel_path):
        # 优先从缓存中读取
        if rel_path in self.dates_cache:
            return datetime.fromisoformat(self.dates_cache[rel_path]['created'])
        
        # 获取文件系统时间
        stat = os.stat(file_path)
        system = platform.system().lower()
        fs_time = None
        if system.startswith('win'):  # Windows
            fs_time = datetime.fromtimestamp(stat.st_ctime)
        elif system == 'darwin':  # macOS
            try:
                fs_time = datetime.fromtimestamp(stat.st_birthtime)
            except AttributeError:
                fs_time = datetime.fromtimestamp(stat.st_ctime)
        else:  # Linux, 没有创建时间，使用修改时间
            fs_time = datetime.fromtimestamp(stat.st_mtime)
        
        # 获取Git首次提交时间
        git_time = self._get_git_first_commit_time(file_path)
        
        # 取两者更早的时间
        if git_time is not None:
            return min(fs_time, git_time)
        return fs_time

    def _get_file_modification_time(self, file_path):
        """
        # 从git获取最后修改时间
        if self.is_git_repo:
            try:
                # 获取文件最后修改时间
                cmd = f'git log -1 --format="%aI" --date=iso -- "{file_path}"'
                process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if process.returncode == 0 and process.stdout.strip():
                    git_time = process.stdout.strip()
                    return datetime.fromisoformat(git_time).replace(tzinfo=None)
            except Exception as e:
                logging.warning(f"Failed to get git modification time: {str(e)}")
        """

        # 从文件系统获取最后修改时间
        stat = os.stat(file_path)
        return datetime.fromtimestamp(stat.st_mtime)


    def _process_meta_author(self, meta):
        try:
            # 1. 处理 author 对象，或 author 字符串
            author_data = meta.get('author')
            if author_data:
                if isinstance(author_data, dict):
                    name = str(author_data.get('name', ''))
                    if not name:
                        return None
                    email = str(author_data.get('email', ''))
                    # 提取扩展属性
                    extra_attrs = {k: str(v) for k, v in author_data.items() 
                                if k not in ['name', 'email']}
                    return Author(name=name, email=email, **extra_attrs)
                return Author(name=str(author_data))
            
            # 2. 处理独立字段，匹配 author_field_mapping 配置
            name = ''
            email = ''
            
            for name_field in self.config['author_field_mapping']['name']:
                if name_field in meta:
                    name = str(meta[name_field])
                    break
            
            for email_field in self.config['author_field_mapping']['email']:
                if email_field in meta:
                    email = str(meta[email_field])
                    break
            
            if name or email:
                if not name and email:
                    name = email.split('@')[0]
                return Author(name=name, email=email)
        except Exception as e:
            logging.warning(f"Error processing author meta: {e}")
        return None

    def _get_git_authors(self, file_path: str) -> Union[Author, List[Author], None]:
        if not self.is_git_repo:
            return None
        try:
            # # 检查文件是否在 Git 中
            # check_file = subprocess.run(f'git ls-files --error-unmatch {file_path}',
            #                           shell=True, capture_output=True, text=True)
            # if check_file.returncode != 0:
            #     return None

            # 获取作者信息（为了兼容性，不采用管道命令，在 python 中处理去重）
            # git_log_cmd = f'git log --format="%an|%ae" -- {file_path} | sort | uniq'
            # git_log_cmd = f'git log --format="%an|%ae" -- {file_path} | grep -vE "bot|noreply|ci|github-actions|dependabot|renovate" | sort | uniq'            
            git_log_cmd = ['git', 'log', '--format=%an|%ae', '--', file_path]
            git_log_result = subprocess.run(git_log_cmd, capture_output=True, text=True, check=False)
            if git_log_result.returncode != 0 or not git_log_result.stdout.strip():
                return None
            
            authors = []
            unique_entries = set()
            for line in git_log_result.stdout.strip().splitlines():
                if not line or line in unique_entries:
                    continue
                unique_entries.add(line)
                name, email = line.split('|')
                authors.append(Author(name=name, email=email))
            
            if not authors:
                return None
            
            return authors[0] if len(authors) == 1 else authors
        except Exception as e:
            logging.warning(f"Failed to get git author info: {str(e)}")
        return None

    def _get_local_author(self):
        username = Path.home().name
        return Author(name=username)


    def _get_formatted_date(self, date):
        if self.config['type'] == 'timeago':
            return ""
        elif self.config['type'] == 'datetime':
            return date.strftime(f"{self.config['date_format']} {self.config['time_format']}")
        return date.strftime(self.config['date_format'])

    def _generate_html_info(self, created, modified, author=None):
        html = ""
        try:
            locale = 'zh_CN' if self.config['locale'] == 'zh' else self.config['locale']
            position_class = 'document-dates-top' if self.config['position'] == 'top' else 'document-dates-bottom'
            
            # 构建基本的日期信息 HTML
            html += (
                f"<div class='document-dates-plugin-wrapper {position_class}'>"
                f"<div class='document-dates-plugin'>"
                f"<span data-tippy-content='{self.translation.get('created_time', 'Created')}: {created.strftime(self.config['date_format'])}'>"
                f"<span class='material-icons' data-icon='doc_created'></span>"
                f"<time datetime='{created.isoformat()}' locale='{locale}'>{self._get_formatted_date(created)}</time></span>"
                f"<span data-tippy-content='{self.translation.get('modified_time', 'Last Update')}: {modified.strftime(self.config['date_format'])}'>"
                f"<span class='material-icons' data-icon='doc_modified'></span>"
                f"<time datetime='{modified.isoformat()}' locale='{locale}'>{self._get_formatted_date(modified)}</time></span>"
            )
            
            # 添加作者信息
            if self.config['show_author'] and author:
                if isinstance(author, list):
                    # 多个作者的情况
                    authors_info = ', '.join(a.name for a in author if a.name)
                    authors_tooltip = ',&nbsp;'.join(f'<a href="mailto:{a.email}">{a.name}</a>' if a.email else a.name for a in author)
                    
                    html += (
                        f"<span data-tippy-content='{self.translation.get('authors', 'Authors')}: {authors_tooltip}'>"
                        f"<span class='material-icons' data-icon='doc_authors'></span>"
                        f"{authors_info}</span>"
                        # f"{authors_tooltip}</span>"
                    )
                else:
                    # 单个作者的情况
                    author_tooltip = f'<a href="mailto:{author.email}">{author.name}</a>' if author.email else author.name
                    html += (
                        f"<span data-tippy-content='{self.translation.get('author', 'Author')}: {author_tooltip}'>"
                        f"<span class='material-icons' data-icon='doc_author'></span>"
                        f"{author.name}</span>"
                        # f"{author_tooltip}</span>"
                    )
            
            html += f"</div></div>"
        
        except Exception as e:
            logging.warning(f"Error generating HTML info: {e}")
        return html


    def _insert_date_info(self, markdown, date_info):
        if not markdown.strip():
            return markdown

        if self.config['position'] == 'top':
            lines = markdown.splitlines()
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    lines.insert(i + 1, date_info)
                else:
                    lines.insert(0, date_info)
                return '\n'.join(lines)
            return f"{date_info}\n{markdown}"
        return f"{markdown}\n\n{date_info}"
