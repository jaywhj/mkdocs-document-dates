# mkdocs-document-dates

English | [简体中文](README_zh.md)

<br />

A new generation MkDocs plugin for displaying exact **creation date, last updated date, authors, email** of documents

![render](render.gif)

## Features

- [x] Works in any environment: no-Git, Git environments, Docker, all CI/CD build systems, etc.
- [x] Support list display of recently updated documents (in descending order of update date)
- [x] Support for manually specifying date and author in `Front Matter`
- [x] Support for multiple date formats (date, datetime, timeago)
- [x] Support for multiple author modes (avatar, text, hidden)
- [x] Support for manually configuring author's name, link, avatar, email, etc.
- [x] Flexible display position (top or bottom)
- [x] Elegant styling (fully customizable)
- [x] Multi-language support, localization support, intelligent recognition of user language, automatic adaptation
- [x] **Ultimate build efficiency**: O(1), no need to set the env var `!ENV` to distinguish runs

| Build Speed Comparison:     | 100 md: | 1000 md: | Time Complexity: |
| --------------------------- | :-----: | :------: | :----------: |
| git-revision-date-localized<br />git-authors |  ＞ 3 s   |  ＞ 30 s   |    O(n)    |
| document-dates              | < 0.1 s  | < 0.15 s  |    O(1)    |

## Installation

```bash
pip install mkdocs-document-dates
```

## Configuration

Just add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - document-dates
```

Or, common configuration:

```yaml
plugins:
  - document-dates:
      position: top            # Display position: top(after title) bottom(end of document), default: top
      type: date               # Date type: date datetime timeago, default: date
      exclude:                 # List of excluded files (support unix shell-style wildcards)
        - temp.md                  # Example: exclude the specified file
        - blog/*                   # Example: exclude all files in blog folder, including subfolders
        - '*/index.md'             # Example: exclude all index.md files in any subfolders
```

## Customization Settings

In addition to the above basic configuration, the plug-in also provides a wealth of customization options to meet a variety of individual needs:

- [Date & Time](https://jaywhj.netlify.app/document-dates-en#Date--Time): Introduces the mechanism for obtaining document dates and methods for personalized customization, support for manually specifying the creation date and last updated date for each document
- [Author](https://jaywhj.netlify.app/document-dates-en#Author): Introduces the mechanism for obtaining document authors and methods for personalized customization, support for manually specifying the author information for each document, such as name, link, avatar, email, etc.
- [Avatar](https://jaywhj.netlify.app/document-dates-en#Avatar): You can manually specify the avatar for each author, support local file path and URL path
- [Structure and Style](https://jaywhj.netlify.app/document-dates-en#Structure-and-Style): You can freely configure the plugin's display structure in mkdocs.yml or Front Matter. You can quickly set the plugin styles through preset entrances, such as icons, themes, colors, fonts, animations, dividing line and so on
- [Template Variables](https://jaywhj.netlify.app/document-dates-en#Template-Variables): Can be used to optimize `sitemap.xml` for site SEO
- [Recently Updated Module](https://jaywhj.netlify.app/document-dates-en#Recently-Updated-Module): Enable list of recently updated documents (in descending order of update date), this is ideal for sites with a large number of documents, so that readers can quickly see what's new
- [Localization Language](https://jaywhj.netlify.app/document-dates-en#Localization-Language): More localization languages for `timeago` and `tooltip` 
- [Development Stories](https://jaywhj.netlify.app/document-dates-en#Development-Stories): Describes the origin of the plug-in, the difficulties and solutions encountered in development, and the principles and directions of product design

See the documentation for details: https://jaywhj.netlify.app/document-dates-en

![recently-updated](recently-updated-en.gif)

## Other Projects

- [**MaterialX**](https://github.com/jaywhj/mkdocs-materialx), the next generation of mkdocs-material. Build beautiful sites the way you already know and love. Based on `mkdocs-material-9.7.1` and is named `X`, it provides ongoing maintenance and updates (since mkdocs-material will stop being maintained).  
Updates have been released that refactor and add a lot of new features, see https://github.com/jaywhj/mkdocs-materialx/releases/

<br />

## Chat Group

**Discord**: https://discord.gg/cvTfge4AUy

**Wechat**: 

<img src="wechat-group.jpg" width="140" />