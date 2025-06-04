# mkdocs-document-dates

[English](README.md) | 简体中文



一个用于显示文档的<mark>准确</mark>创建日期和最后修改日期的 MkDocs 插件。

## 特性

- **不依赖 Git**，使用文件系统时间戳，适用于任何环境
- 支持在 `Front Matter` 中手动指定日期
- 支持多种时间格式（date、datetime、timeago）
- 支持文档排除模式
- 灵活的显示位置（顶部或底部）
- Material 风格的图标，优雅的样式设计（支持自定义）
- 支持 Tooltip 悬浮提示
  - 智能位置调整，始终以最佳方式浮动在视图中
  - 支持主题跟随 Material 亮/暗配色变化而变化
  - 支持自定义主题、样式、动画等
  - 兼容鼠标、键盘和**触摸**（移动端）触发 hover
- 支持 CI/CD 构建系统（如 Github Actions）
- 多语言支持，跨平台支持（Windows、macOS、Linux）


## 效果图

![render](render.gif)

## 安装

```bash
pip install mkdocs-document-dates
```

## 配置

在你的 mkdocs.yml 中添加插件即可：

```yaml
plugins:
  - document-dates
```

或者，你要自定义配置：

```yaml
plugins:
  - document-dates:
      type: date               # 日期类型：date datetime timeago，默认：date
      locale: zh               # 本地化语言：zh zh_tw en es fr de ar ja ko ru，默认：en
      date_format: '%Y-%m-%d'  # 日期格式，支持所有Python日期格式化字符串，例如：%Y年%m月%d日、%b %d, %Y
      time_format: '%H:%M:%S'  # 时间格式（仅在 type=datetime 时有效）
      position: bottom         # 显示位置：top（标题后） bottom（文档末尾），默认：bottom
      exclude:                 # 排除文件列表，默认为空
        - temp.md              # 排除指定文件
        - private/*            # 排除 private 目录下的所有文件，包括子目录
        - drafts/*.md          # 排除当前目录 drafts 下的所有 markdown 文件，不包括子目录

```

## 手动指定日期

你也可以在 Markdown 文档的 `Front Matter` 中手动指定该文档的日期：

```yaml
---
created: 2023-01-01
modified: 2025-02-23
---

# 文档标题
```

- `created` 可替换为：`created, date, creation_date, created_at, date_created`
- `modified` 可替换为：`modified, updated, last_modified, updated_at, last_update`

## 自定义

插件支持深度自定义，直接修改对应文件中的代码即可：

- 样式与主题：`docs/assets/document_dates/document-dates.config.css`
- 属性与动画：`docs/assets/document_dates/document-dates.config.js`
- 本地化语言：`docs/assets/document_dates/languages/` ，可根据模板文件 `en.json` 进行修改或新增

提示：如果要恢复默认效果，直接删除此文件，然后重新 build 即可！

## 小贴士

- 在使用 CI/CD 构建系统时（比如 Github Actions），它仍然有效，以下是操作流程：
    1. 首先，你可以这么配置工作流（倒数第二行），在你的 `.github/workflows/ci.yml` 中：
    ```
    ...
    
        - run: pip install mkdocs-document-dates
        - run: mkdocs gh-deploy --force
    ```
    2. 然后正常的更新 `docs` 中的 Markdown 文档
    3. 执行 git add 和 git commit 后，就能在 `docs` 目录下看到自动生成的缓存文件 `.dates_cache.json`（默认是隐藏的）
        - 确保已经提前安装了 python3 且设置了环境变量
    4. 最后，执行 git push，就可以看到 GitHub 仓库中 docs 目录下也存在 `.dates_cache.json` 文件，即表示成功
- 时间读取的优先级：
    - `Front Matter` > `缓存文件` > `文件系统时间戳` 
- 如果你是在 Linux 系统下使用 MkDocs ，因为系统限制，使用修改时间作为创建时间，如果需要准确的创建时间，可在 Front Matter 中手动指定