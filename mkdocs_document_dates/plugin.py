import os
import json
import shutil
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from .cache_manager import read_json_cache, read_jsonl_cache, get_file_creation_time, get_git_first_commit_time

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
        ('locale', config_options.Type(str, default=None)),
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
        try:
            # 设置 locale 在无配置时跟随主题语言
            if not self.config['locale']:
                self.config['locale'] = config['theme']['language']
        except Exception:
            self.config['locale'] = 'en'

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
        self.dates_cache = read_jsonl_cache(jsonl_cache_file)

        # 兼容旧版缓存文件
        if not self.dates_cache:
            json_cache_file = docs_dir_path / '.dates_cache.json'
            self.dates_cache = read_json_cache(json_cache_file)

        """
        Tippy.js
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
        dest_dir = docs_dir_path / 'assets' / 'document_dates'
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for dir_name in ['tippy', 'core']:
            source_dir = Path(__file__).parent / 'static' / dir_name
            target_dir = dest_dir / dir_name
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
        
        # 复制配置文件模板到用户目录（如果不存在）
        config_files = ['user.config.css', 'user.config.js']
        for config_file in config_files:
            source_config = Path(__file__).parent / 'static' / 'config' / config_file
            target_config = dest_dir / config_file
            if not target_config.exists():
                shutil.copy2(source_config, target_config)

        
        # 加载图标 Google Fonts Icons: https://fonts.google.com/icons
        material_icons_url = 'https://fonts.googleapis.com/icon?family=Material+Icons'
        if material_icons_url not in config['extra_css']:
            config['extra_css'].append(material_icons_url)
        
        # 加载 timeago.js
        # https://cdn.jsdelivr.net/npm/timeago.js@4.0.2/dist/timeago.min.js
        # https://cdnjs.cloudflare.com/ajax/libs/timeago.js/4.0.2/timeago.full.min.js
        if self.config['type'] == 'timeago':
            config['extra_javascript'][0:0] = [
                'assets/document_dates/core/timeago.min.js',
                'assets/document_dates/core/timeago-load.js'
            ]

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
        # 获取相对路径，src_uri 总是以"/"分隔
        rel_path = getattr(page.file, 'src_uri', None)
        if not rel_path:
            rel_path = page.file.src_path
            if os.sep != '/':
                rel_path = rel_path.replace(os.sep, '/')
        file_path = page.file.abs_src_path
        
        # 获取时间信息
        created = self._find_meta_date(page.meta, self.config['created_field_names'])
        modified = self._find_meta_date(page.meta, self.config['modified_field_names'])
        if not created:
            created = self._get_file_creation_time(file_path, rel_path)
        if not modified:
            modified = self._get_file_modification_time(file_path)
        
        # 获取作者信息
        authors = self._get_author_info(file_path, page, config)
        
        # 在排除前暴露 meta 信息给前端使用
        page.meta['document_dates_created'] = created.isoformat()
        page.meta['document_dates_modified'] = modified.isoformat()
        page.meta['document_dates_authors'] = authors
        
        # 检查是否需要排除
        if self._is_excluded(rel_path):
            return markdown
        
        # 生成日期和作者信息 HTML
        info_html = self._generate_html_info(created, modified, authors)
        
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


    def _is_excluded(self, rel_path):
        for pattern in self.config['exclude']:
            # if fnmatch.fnmatch(rel_path, pattern):
            if self._matches_exclude_pattern(rel_path, pattern):
                return True
        return False

    def _matches_exclude_pattern(self, rel_path, pattern):
        if '*' not in pattern:
            return rel_path == pattern
        else:
            return rel_path.startswith(pattern.partition('*')[0])


    def _find_meta_date(self, meta, field_names):
        for field in field_names:
            if field in meta:
                try:
                    # 移除首尾可能存在的单双引号和时区信息
                    date_str = str(meta[field]).strip("'\"")
                    return datetime.fromisoformat(date_str).replace(tzinfo=None)
                except Exception:
                    continue
        return None

    def _get_file_creation_time(self, file_path, rel_path):
        # 优先从缓存中读取
        if rel_path in self.dates_cache:
            return datetime.fromisoformat(self.dates_cache[rel_path]['created'])
        
        # 从文件系统获取
        fs_time = get_file_creation_time(file_path)
        
        # 获取Git首次提交时间
        if self.is_git_repo:
            git_time = get_git_first_commit_time(file_path)
            # 取两者更早的时间
            if git_time:
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


    def _get_author_info(self, file_path, page, config):
        if not self.config['show_author']:
            return None
        # 1. meta author
        authors = self._process_meta_author(page.meta)
        if authors:
            return authors
        # 2. git author
        authors = self._get_git_authors(file_path)
        if authors:
            return authors
        # 3. site_author 或 PC username
        return [Author(name=config.get('site_author') or Path.home().name)]

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
                    return [Author(name=name, email=email, **extra_attrs)]
                return [Author(name=str(author_data))]
            
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
                    name = email.partition('@')[0]
                return [Author(name=name, email=email)]
        except Exception as e:
            logging.warning(f"Error processing author meta: {e}")
        return None

    def _get_git_authors(self, file_path):
        if not self.is_git_repo:
            return None
        try:
            # 获取作者信息（为了兼容性，不采用管道命令，在 python 中处理去重）
            # git_log_cmd = f'git log --format="%an|%ae" -- {file_path} | sort | uniq'
            # git_log_cmd = f'git log --format="%an|%ae" -- {file_path} | grep -vE "bot|noreply|ci|github-actions|dependabot|renovate" | sort | uniq'            
            git_log_cmd = ['git', 'log', '--format=%an|%ae', '--', file_path]
            git_log_result = subprocess.run(git_log_cmd, capture_output=True, text=True, check=False)
            if git_log_result.returncode != 0 or not git_log_result.stdout.strip():
                return None
            
            # 使用字典去重和存储作者
            authors_map = {}
            for line in git_log_result.stdout.splitlines():
                if not line.strip() or line in authors_map:
                    continue
                name, email = line.split('|')
                authors_map[line] = Author(name=name, email=email)

            return list(authors_map.values()) or None
        except Exception as e:
            logging.warning(f"Failed to get git author info: {str(e)}")
        return None


    def _get_formatted_date(self, date):
        if self.config['type'] == 'timeago':
            return ""
        elif self.config['type'] == 'datetime':
            return date.strftime(f"{self.config['date_format']} {self.config['time_format']}")
        return date.strftime(self.config['date_format'])

    def _generate_html_info(self, created, modified, authors=None):
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
            if self.config['show_author'] and authors:
                if len(authors) == 1:
                    author, = authors
                    author_tooltip = f'<a href="mailto:{author.email}">{author.name}</a>' if author.email else author.name
                    html += (
                        f"<span data-tippy-content='{self.translation.get('author', 'Author')}: {author_tooltip}'>"
                        f"<span class='material-icons' data-icon='doc_author'></span>"
                        f"{author.name}</span>"
                        # f"{author_tooltip}</span>"
                    )
                else:
                    # 多个作者的情况
                    authors_info = ', '.join(a.name for a in authors if a.name)
                    authors_tooltip = ',&nbsp;'.join(f'<a href="mailto:{a.email}">{a.name}</a>' if a.email else a.name for a in authors)
                    
                    html += (
                        f"<span data-tippy-content='{self.translation.get('authors', 'Authors')}: {authors_tooltip}'>"
                        f"<span class='material-icons' data-icon='doc_authors'></span>"
                        f"{authors_info}</span>"
                        # f"{authors_tooltip}</span>"
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
