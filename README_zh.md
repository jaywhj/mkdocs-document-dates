# mkdocs-document-dates

[English](README.md) | 简体中文



一个用于显示文档的<mark>准确</mark>创建时间、最后更新时间及作者信息的 MkDocs 插件，简单易用、轻量智能。

## 特性

- 适用于任何环境，适配无 Git 环境、CI/CD 环境（比如 GitHub Actions）、一人协作、多人协作等所有场景
- 支持在 `Front Matter` 中手动指定时间和作者信息
- 支持多种时间格式（date、datetime、timeago）
- 支持文档排除模式
- 灵活的显示位置（顶部或底部）
- 优雅的样式设计（完全可定制）
- 支持 Tooltip 悬浮提示
  - 智能位置调整，始终以最佳方式浮动在视图中
  - 支持主题跟随 Material 亮/暗配色变化而变化
  - 支持自定义主题、样式、动画等
  - 兼容鼠标、键盘和**触摸**（移动端）触发 hover
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

或者，你要个性化配置：

```yaml
plugins:
  - document-dates:
      position: top            # 显示位置：top（标题后） bottom（文档末尾），默认：bottom
      type: date               # 时间类型：date datetime timeago，默认：date
      locale: zh               # 本地化语言：zh zh_tw en es fr de ar ja ko ru，默认：en
      date_format: '%Y-%m-%d'  # 日期格式，支持所有Python日期格式化字符串，例如：%Y年%m月%d日、%b %d, %Y
      time_format: '%H:%M:%S'  # 时间格式（仅在 type=datetime 时有效）
      exclude:                 # 排除文件列表，默认为空
        - temp.md              # 排除指定文件
        - private/*            # 排除 private 目录下的所有文件，包括子目录
        - drafts/*.md          # 排除当前目录 drafts 下的所有 markdown 文件，不包括子目录
      
      show_author: true        # 是否显示作者信息：true false，默认：true

```

## 手动指定时间

插件会自动获取文档的准确时间信息，会自动缓存创建时间，当然，你也可以在 `Front Matter` 中手动指定

优先级：`Front Matter` > `缓存文件` > `文件系统时间戳` 

```yaml
---
created: 2023-01-01
modified: 2025-02-23
---

# 文档标题
```

- `created` 可替换为：`created, date, creation`
- `modified` 可替换为：`modified, updated, last_modified, last_updated`

## 手动指定作者

插件会自动获取文档的作者信息，会解析邮件后做链接，你也可以在 `Front Matter` 中手动指定

优先级：`Front Matter` > `Git作者信息` > `PC用户名` 

```yaml
---
author: any-name
email: e-name@gmail.com
---

# 文档标题
```

- `author` 可替换为：`author, name`
- `email` 可替换为：`email, mail`

## 插件定制化

插件支持深度自定义，比如**图标样式、字体风格、主题颜色、动画类型、分割线**等等，所有的一切都可以自定义，修改对应文件中的代码即可（我已经写好了代码和注释，你只需要打开开关，改个值就行，超简单）：

- 样式与主题：`docs/assets/document_dates/user.config.css`
- 属性与动画：`docs/assets/document_dates/user.config.js`
- 本地化语言：`docs/assets/document_dates/languages/` ，可参考模板文件 `en.json` 任意新增或修改

*注意：由于重新设计了配置文件的更新机制，上版本中 document-dates.config 开头的配置文件取消了，换成了 user.config*

## 其它提示

- 为了获取准确的创建时间，采用了单独的缓存文件来存储文件的创建时间，位于 doc 目录下（默认是隐藏的），请不要删除：
    - `docs/.dates_cache.jsonl`，缓存文件（不带 l 的 .json 是旧缓存文件，任意一次 git commit 后会自动迁移到 .jsonl 中）
    - `docs/.gitattributes`，配置文件（多人协作时缓存文件的合并机制）
- 采用了 Git Hooks 机制来自动触发缓存的存储（在每次执行 git commit 时），缓存文件也会随之自动提交
- 在插件被安装时，会自动触发 Git Hooks 的安装
- 以上动作全自动化处理，无需任何手动干预，适用于任何环境，已在无 Git 环境、CI/CD 环境（比如 GitHub Actions）、一人协作、多人协作等场景下测试验证

<br />

## 开发小故事（可选）

一个可有可无、微不足道的小插件，没事的朋友可以看看 \^\_\^ 

- **起源**：
    - 是因为 [mkdocs-git-revision-date-localized-plugin](https://github.com/timvink/mkdocs-git-revision-date-localized-plugin) ，一个很棒的项目。在2024年底使用时，发现我这本地用不了，因为我的 mkdocs 文档没有纳入 git 管理，然后我就不理解为什么不读取文件系统的时间，而要用 git 时间，还给作者提了 issue，结果等了一周左右没得到回复（后面作者回复了，人不错，估计他当时在忙没来得及），然后就想，过年期间没啥事，现在 AI 这么火，要不借助 AI 自己试试，就诞生了，诞生于2025年2月
- **迭代**：
    - 开发后，就理解了为什么不采用文件系统时间，因为文件在经过 git checkout 或 clone 时会被重建，从而导致原始时间戳信息丢失，解决办法有很多：
    - 方法 1，采用最近一次 git commit 时间作为文档的最后更新时间，采用首次 git commit 时间作为文档的创建时间（虽然有误差，但能接受），mkdocs-git-revision-date-localized-plugin 就是这么做的
    - 方法 2，可以缓存原始时间信息，后续读缓存就可以了。缓存的地方，可以是源文档的 Front Matter 中，也可以是单独的文件，我选择了后者。存在 Front Matter 中非常合理和简单，但是这样会修改文档的源内容，虽然对正文无任何影响，但是我还是想保证数据的原始性
- **难点**：
    1. 什么时候读取和存储原始时间？这只是 mkdocs 的一个插件，入口和权限非常有限，mkdocs 提供的只有 build 和 serve，那万一用户不执行 build 或 serve 而直接 commit 呢（比如使用 CI/CD 构建系统时），那就拿不到文件的时间信息了，更别说缓存了
        - 直接说结论：在 AI 的提示下，找到了 Git Hooks 机制，能在特定的动作发生时触发自定义脚本，比如每次 commit 时
    2. 单独的缓存文件，在多人协作时，如何保证缓存文件不冲突？
        - 我的方案：采用 JSONL（JSON Lines）代替 JSON，配合并集的合并策略 merge=union
- **精进**：
    - 既然重新开发，那就奔着**优秀产品**的方向去设计，追求极致的**易用性、简洁性、个性化**
        - 易用性：能不让用户手动操作的就不让手动，比如自动安装 Git Hooks、自动缓存、自动 commit，提供自定义模板等
        - 简洁性：无任何多余的不必要的配置，越少越简单，比如 git 账户信息、repo 信息等，都不需要
        - 个性化：几乎所有地方都可以自定义，无论是图标、样式、主题，还是功能，都可实现完全定制化
    - 此外还有很好的兼容性和扩展性，在 WIN7、移动设备、旧版 Safari 等环境下均能正常运行
- **最后的秘密**：
    - 我不是程序员，主业是市场营销，你信吗？（欢迎留言）