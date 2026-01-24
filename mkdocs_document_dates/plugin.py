import os
import yaml
import shutil
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from pathlib import Path
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.structure.pages import Page
from mkdocs.utils import get_relative_url
from urllib.parse import urlparse
from .utils import get_file_creation_time, load_git_metadata, load_git_last_updated_date, read_jsonl_cache,is_excluded, get_recently_updated_files

logger = logging.getLogger("mkdocs.plugins.document_dates")
logger.setLevel(logging.WARNING)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class Author:
    def __init__(self, name="", email="", avatar="", url="", description="", **kwargs):
        self.name = name
        self.email = email
        self.avatar = avatar
        self.url = url
        self.description = description


class DocumentDatesPlugin(BasePlugin):
    config_scheme = (
        ('type', config_options.Type(str, default='date')),
        ('locale', config_options.Type(str, default='')),
        ('date_format', config_options.Type(str, default='%Y-%m-%d')),
        ('time_format', config_options.Type(str, default='%H:%M:%S')),
        ('position', config_options.Type(str, default='top')),
        ('exclude', config_options.Type(list, default=[])),
        ('created_field_names', config_options.Type(list, default=['created', 'date'])),
        ('updated_field_names', config_options.Type(list, default=['updated', 'modified'])),
        ('show_created', config_options.Type(bool, default=True)),
        ('show_updated', config_options.Type(bool, default=True)),
        ('show_author', config_options.Choice((True, False, 'text'), default=True)),
        ('recently-updated', config_options.Type((dict, bool), default={}))
    )

    def __init__(self):
        super().__init__()
        self.dates_cache = {}
        self.last_updated_dates = {}
        self.authors_yml = {}
        self.recent_docs_html = None
        self.recent_enable = False

    def on_config(self, config):
        docs_dir_path = Path(config['docs_dir'])

        # 加载 author 配置
        authors_file = docs_dir_path / 'authors.yml'
        if not authors_file.exists():
            try:
                blog_config = config['plugins']['material/blog'].config
                authors_file_resolved = blog_config.authors_file.format(blog=blog_config.blog_dir)
                authors_file = docs_dir_path / authors_file_resolved
            except Exception:
                pass
        self._load_authors_from_yaml(authors_file)

        # 加载文档元数据
        self.dates_cache = load_git_metadata(docs_dir_path)
        # 覆盖 jsonl 缓存
        jsonl_cache_file = docs_dir_path / '.dates_cache.jsonl'
        if jsonl_cache_file.exists():
            jsonl_cache = read_jsonl_cache(jsonl_cache_file)
            for filename, new_info in jsonl_cache.items():
                if filename in self.dates_cache:
                    self.dates_cache[filename].update(new_info)

        # 加载文档最近更新时间
        self.last_updated_dates = load_git_last_updated_date(docs_dir_path)


        # 复制配置文件到用户目录（如果不存在）
        dest_dir = docs_dir_path / 'assets' / 'document_dates'
        dest_dir.mkdir(parents=True, exist_ok=True)
        config_files = ['user.config.css', 'user.config.js']
        for config_file in config_files:
            source_config = Path(__file__).parent / 'static' / 'config' / config_file
            target_config = dest_dir / config_file
            if not target_config.exists():
                shutil.copy2(source_config, target_config)

        # 添加离线 Google Fonts Icons: https://fonts.google.com/icons
        # material_icons_url = 'https://fonts.googleapis.com/icon?family=Material+Icons'
        material_icons_url = 'assets/document_dates/fonts/material-icons.css'
        config['extra_css'].append(material_icons_url)

        # 添加 timeago.js
        # https://cdn.jsdelivr.net/npm/timeago.js@4.0.2/dist/timeago.min.js
        # https://cdnjs.cloudflare.com/ajax/libs/timeago.js/4.0.2/timeago.full.min.js
        if self.config['type'] == 'timeago':
            config['extra_javascript'].insert(0, 'assets/document_dates/core/timeago.min.js')

        """
        Tippy.js, for Tooltip
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
        # 添加 Tippy CSS 文件
        tippy_css_dir = Path(__file__).parent / 'static' / 'tippy'
        for css_file in tippy_css_dir.glob('*.css'):
            config['extra_css'].append(f'assets/document_dates/tippy/{css_file.name}')
        
        # 添加自定义 CSS 文件
        config['extra_css'].extend([
            'assets/document_dates/core/core.css',
            'assets/document_dates/user.config.css'
        ])
        
        # 按顺序添加 Tippy JS 文件
        js_core_files = ['popper.min.js', 'tippy.umd.min.js']
        for js_file in js_core_files:
            config['extra_javascript'].append(f'assets/document_dates/tippy/{js_file}')
        
        # 添加自定义 JS 文件
        config['extra_javascript'].extend([
            'assets/document_dates/core/md5.min.js',
            'assets/document_dates/core/default.config.js',
            'assets/document_dates/user.config.js',
            'assets/document_dates/core/utils.js',
            'assets/document_dates/core/core.js'
        ])

        return config

    def on_page_markdown(self, markdown, page: Page, config, files):
        # 获取相对路径，src_uri 总是以"/"分隔
        rel_path = getattr(page.file, 'src_uri', page.file.src_path)
        if os.sep != '/':
            rel_path = rel_path.replace(os.sep, '/')
        file_path = page.file.abs_src_path
        
        # 获取时间信息
        created = self._find_meta_date(page.meta, self.config['created_field_names'])
        updated = self._find_meta_date(page.meta, self.config['updated_field_names'])
        if not created:
            created = self._get_file_creation_time(file_path, rel_path)
        if not updated:
            updated = self._get_file_modification_time(file_path, rel_path)
        
        # 获取作者信息
        authors = self._get_author_info(rel_path, page, config)
        
        # 在排除前暴露 meta 信息给前端使用
        page.meta['document_dates_created'] = created.isoformat()
        page.meta['document_dates_updated'] = updated.isoformat()
        page.meta['document_dates_authors'] = authors
        
        # 检查是否需要排除
        if is_excluded(rel_path, self.config['exclude']):
            return markdown
        
        # 生成日期和作者信息 HTML
        info_html = self._generate_html_info(page.meta, created, updated, authors)
        
        # 将信息写入 markdown
        return self._insert_date_info(markdown, info_html)

    def on_env(self, env, config, files):
        recently_updated_config = self.config.get('recently-updated')
        if recently_updated_config:
            self.recent_enable = True

        # 兼容 true 配置
        if recently_updated_config is True:
            recently_updated_config = {}

        # 获取配置
        exclude_list = recently_updated_config.get('exclude', [])
        limit = recently_updated_config.get('limit', 10)

        # 获取最近更新的文档数据
        recently_updated_docs = get_recently_updated_files(self.last_updated_dates, files, exclude_list, limit, self.recent_enable)

        # 将数据注入到 config['extra'] 中供全局访问
        if 'extra' not in config:
            config['extra'] = {}
        config['extra']['recently_updated_docs'] = recently_updated_docs

        # 渲染HTML
        if self.recent_enable:
            self.recent_docs_html = self._render_recently_updated_html(recently_updated_docs)

        return env

    def on_post_page(self, output, page, config):
        if self.recent_enable and '\n<!-- RECENTLY_UPDATED_DOCS -->' in output:
            output = output.replace('\n<!-- RECENTLY_UPDATED_DOCS -->', self.recent_docs_html or '')

        return output

    def on_post_build(self, config):
        site_dest_dir = Path(config['site_dir']) / 'assets' / 'document_dates'
        for dir_name in ['tippy', 'core', 'fonts']:
            source_dir = Path(__file__).parent / 'static' / dir_name
            target_dir = site_dest_dir / dir_name
            # shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            target_dir.mkdir(parents=True, exist_ok=True)
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, target_dir / item.name)


    def _load_authors_from_yaml(self, file_path: Path):
        if not file_path.exists():
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            for key, info in (data or {}).get('authors', {}).items():
                self.authors_yml[key] = Author(**info)
        except Exception as e:
            logger.info(f"Error parsing .authors.yml: {e}")


    def _render_recently_updated_html(self, recently_updated_data):
        default_template_path = Path(__file__).parent / 'static' / 'templates' / 'recently_updated_group.html'
        template_dir = default_template_path.parent
        template_file = default_template_path.name

        # 加载模板
        env = Environment(
            loader = FileSystemLoader(str(template_dir)),
            autoescape = select_autoescape(["html", "xml"])
        )
        template = env.get_template(template_file)

        # 渲染模板
        return template.render(recent_docs=recently_updated_data)


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
        return get_file_creation_time(file_path).astimezone()

    def _get_file_modification_time(self, file_path, rel_path):
        # 优先从缓存中读取
        if rel_path in self.last_updated_dates:
            return datetime.fromtimestamp(self.last_updated_dates[rel_path]).astimezone()
        # 从文件系统获取最后修改时间
        stat = os.stat(file_path)
        return datetime.fromtimestamp(stat.st_mtime).astimezone()


    def _get_author_info(self, rel_path, page, config):
        # 1. meta author
        authors = self._process_meta_author(page.meta, page.url)
        if authors:
            return authors

        # 2. git author
        if rel_path in self.dates_cache:
            authors_list = self.dates_cache[rel_path].get('authors')
            if authors_list:
                authors = []
                for data in authors_list:
                    full_author = self.authors_yml.get(data['name'])
                    if full_author:
                        authors.append(self._get_repaired_author(full_author, page.url))
                    else:
                        authors.append(Author(**data))
                return authors

        # 3. site_author 或 PC username
        name = config.get('site_author') or Path.home().name
        full_author = self.authors_yml.get(name)
        if full_author:
            return [self._get_repaired_author(full_author, page.url)]
        else:
            return [Author(name=name)]

    def _process_meta_author(self, meta, page_url):
        try:
            # 匹配 authors 数组
            author_objs = []
            authors_data = meta.get('authors')
            for key in authors_data or []:
                full_author = self.authors_yml.get(key)
                if full_author:
                    author_objs.append(self._get_repaired_author(full_author, page_url))
                else:
                    author_objs.append(Author(name=str(key)))
            if author_objs:
                return author_objs

            # 匹配独立字段: name, email
            name = meta.get('name')
            email = meta.get('email')
            if name or email:
                if not name and email:
                    name = email.partition('@')[0]
                full_author = self.authors_yml.get(name)
                if full_author:
                    return [self._get_repaired_author(full_author, page_url)]
                else:
                    return [Author(name=name, email=email)]
        except Exception as e:
            logger.warning(f"Error processing author meta: {e}")
        return None

    def _get_repaired_author(self, author: Author, page_url: str) -> Author:
        try:
            if not author.avatar:
                return author
            parsed = urlparse(author.avatar)
            if parsed.scheme or author.avatar.startswith('//'):
                return author
            # 处理本地路径（相对路径 & 绝对路径）
            avatar = get_relative_url(author.avatar.lstrip('/'), page_url or '')
            return Author(**{**vars(author), 'avatar': avatar})
        except Exception:
            return author


    def _get_formatted_date(self, date: datetime):
        if self.config['type'] == 'timeago':
            return ""
        elif self.config['type'] == 'datetime':
            return date.strftime(f"{self.config['date_format']} {self.config['time_format']}")
        return date.strftime(self.config['date_format'])

    def _generate_html_info(self, meta, created: datetime, updated: datetime, authors=None):
        try:
            show_created = self.config['show_created'] and meta.get('show_created') is not False
            show_updated = self.config['show_updated'] and meta.get('show_updated') is not False
            show_author  = self.config['show_author']  and meta.get('show_author')  is not False

            show_dates = show_created or show_updated
            show_plugin = show_dates or show_author
            if not show_plugin:
                return ""

            # 构建插件骨架 HTML
            html_parts = []
            position_class = 'document-dates-top' if self.config['position'] == 'top' else 'document-dates-bottom'
            html_parts.append(f"<div class='document-dates-plugin-wrapper {position_class}'>")
            html_parts.append(f"<div class='document-dates-plugin' locale='{self.config['locale']}'>")

            def build_time_icon(time_obj: datetime, icon: str):
                formatted = time_obj.strftime(self.config['date_format'])
                return (
                    f"<span class='dd-item' data-tippy-content data-tippy-raw='{formatted}'>"
                    f"<span class='material-icons' data-icon='{icon}'></span>"
                    f"<time datetime='{time_obj.isoformat()}'>{self._get_formatted_date(time_obj)}</time>"
                    f"</span>"
                )

            # 构建日期
            if show_dates:
                html_parts.append("<div class='dd-left'>")
            if show_created:
                html_parts.append(build_time_icon(created, 'doc_created'))
            if show_updated:
                html_parts.append(build_time_icon(updated, 'doc_updated'))
            if show_dates:
                html_parts.append("</div>")

            # 构建作者
            if show_author and authors:
                def get_author_tooltip(author):
                    if author.url:
                        return f'<a href="{author.url}" target="_blank">{author.name}</a>'
                    elif author.email:
                        return f'<a href="mailto:{author.email}">{author.name}</a>'
                    return author.name

                if show_dates:
                    html_parts.append("<div class='dd-right'>")
                else:
                    html_parts.append("<div class='dd-right dd-right-start'>")
                icon = 'doc_author' if len(authors) == 1 else 'doc_authors'
                html_parts.append(f"<span class='material-icons' data-icon='{icon}'></span>")
                html_parts.append("<div class='author-group'>")
                show_text = self.config['show_author'] == 'text' or meta.get('show_author') == 'text'
                if show_text:
                    # 显示文本模式
                    for index, author in enumerate(authors):
                        if index > 0:
                            html_parts.append(",&nbsp;&nbsp;")
                        tooltip = get_author_tooltip(author)
                        html_parts.append(f"<span class='text-wrapper' data-tippy-content data-tippy-raw='{ tooltip }'>{ tooltip }</span>")
                else:
                    # 显示头像模式（默认）
                    for author in authors:
                        tooltip = get_author_tooltip(author)
                        html_parts.append(
                            f"<div class='avatar-wrapper' data-name='{author.name}' data-tippy-content data-tippy-raw='{tooltip}'>"
                            f"<span class='avatar-text'></span>"
                            f"<img class='avatar' data-src='{author.avatar}' data-email='{author.email}' />"
                            f"</div>"
                        )
                html_parts.append("</div>")
                html_parts.append("</div>")

            html_parts.append("</div></div>")
            return ''.join(html_parts)

        except Exception as e:
            logger.warning(f"Error generating HTML info: {e}")
            return ""


    def _insert_date_info(self, markdown: str, date_info: str):
        if not date_info:
            return markdown
        if self.config['position'] == 'top':
            first_line, insert_pos = self._find_markdown_body_start(markdown)
            if first_line.startswith(('# ', '<h1')):
                return markdown[:insert_pos] + '\n' + date_info + '\n' + markdown[insert_pos:]
            else:
                return f"{date_info}\n{markdown}"
        return f"{markdown}\n\n{date_info}"

    def _find_markdown_body_start(self, text: str):
        pos = 0
        length = len(text)
        in_comment = False
        WHITESPACE = {' ', '\t', '\r', '\n'}

        while pos < length:
            next_newline = text.find('\n', pos)
            if next_newline == -1:
                next_newline = length

            start = pos
            while start < next_newline and text[start] in WHITESPACE:
                start += 1

            if start < next_newline:
                if not in_comment:
                    if text.startswith('<!--', start):
                        in_comment = True
                        start += 4
                
                if in_comment:
                    comment_end = text.find('-->', start, next_newline)
                    if comment_end != -1:
                        in_comment = False
                        pos = comment_end + 3
                        continue
                    pos = next_newline + 1
                    continue

                # 找到正文行
                return text[start:next_newline], next_newline + 1 if next_newline < length else length

            pos = next_newline + 1

        return '', length