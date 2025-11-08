# mkdocs-document-dates

English | [简体中文](README_zh.md)

<br />

A new generation MkDocs plugin for displaying exact **creation time, last update time, authors, email** of documents

![render](render.gif)

## Features

- [x] Always displays **exact** meta information of the document and works in any environment (no Git, Git environments, Docker containers, all CI/CD build systems, etc.)
- [x] Support list display of recently updated documents (in descending order of update time)
- [x] Support for manually specifying time and author in `Front Matter`
- [x] Support for multiple time formats (date, datetime, timeago)
- [x] Support for multiple author modes (avatar, text, hidden)
- [x] Support for manually configuring author's name, link, avatar, email, etc.
- [x] Flexible display position (top or bottom)
- [x] Elegant styling (fully customizable)
- [x] Smart Tooltip Hover Tips
- [x] Multi-language support, localization support, intelligent recognition of user language, automatic adaptation
- [x] Cross-platform support (Windows, macOS, Linux)
- [x] **Ultimate build efficiency**: O(1), no need to set the env var `!ENV` to distinguish runs

| Build Speed Comparison:     | 100 md: | 1000 md: | Time Complexity: |
| --------------------------- | :-----: | :------: | :----------: |
| git-revision-date-localized |  > 3 s   |  > 30 s   |    O(n)    |
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

Or, full configuration:

```yaml
plugins:
  - document-dates:
      position: top            # Display position: top(after title) bottom(end of document)
      type: date               # Date type: date datetime timeago, default: date
      exclude:                 # List of excluded files
        - temp.md                  # Example: exclude the specified file
        - blog/*                   # Example: exclude all files in blog folder, including subfolders
      date_format: '%Y-%m-%d'  # Date format strings (e.g., %Y-%m-%d, %b %d, %Y)
      time_format: '%H:%M:%S'  # Time format strings (valid only if type=datetime)
      show_author: true        # Author display mode: true(avatar) text(text) false(hidden)
```

## Customization Settings

In addition to the above basic configuration, the plug-in also provides a wealth of customization options to meet a variety of individual needs:

- [Specify Datetime](https://jaywhj.netlify.app/document-dates-en#Specify-Datetime): You can manually specify the creation time and last update time for each document
- [Specify Author](https://jaywhj.netlify.app/document-dates-en#Specify-Author): You can manually specify the author information for each document, such as name, link, avatar, email, etc.
- [Specify Avatar](https://jaywhj.netlify.app/document-dates-en#Specify-Avatar): You can manually specify the avatar for each author
- [Set Plugin Style](https://jaywhj.netlify.app/document-dates-en#Set-Plugin-Style): Such as icons, themes, colors, fonts, animations, dividing line, etc.
- [Add Localization Language](https://jaywhj.netlify.app/document-dates-en#Add-Localization-Language): More localization languages for `timeago` and `tooltip` 
- [Use Template Variables](https://jaywhj.netlify.app/document-dates-en#Use-Template-Variables): Can be used to optimize `sitemap.xml` for site SEO, can be used to re-customize plug-ins, etc.
- [Add Recently Updated Module](https://jaywhj.netlify.app/document-dates-en#Add-Recently-Updated-Module): Enable list of recently updated documents (in descending order of update time)
- [Other Tips](https://jaywhj.netlify.app/document-dates-en#Other-Tips): Introduction to technical principles, caching mechanisms, and how to use it in Docker
- [Development Stories](https://jaywhj.netlify.app/document-dates-en#Development-Stories): Describes the origin of the plug-in, the difficulties and solutions encountered in development, and the principles and directions of product design

See the documentation for details: https://jaywhj.netlify.app/document-dates-en
