# mkdocs-document-dates

English | [简体中文](README_zh.md)



An easy-to-use, lightweight MkDocs plugin for displaying the <mark>exact</mark> creation time, last modification time and author info of markdown documents.

## Features

- Work in any environment, for Git-less environments, CI/CD environments (e.g. GitHub Actions), one-person collaboration, multi-person collaboration, etc
- Support for manually specifying time and author info in `Front Matter`
- Support for multiple time formats (date, datetime, timeago)
- Support for document exclusion mode
- Flexible display position (top or bottom)
- Elegant styling (fully customizable)
- Supports Tooltip Hover Tips
  - Intelligent repositioning to always float optimally in view
  - Supports automatic theme switching following Material's light/dark color scheme
  - Support for customizing themes, styles, animations
  - Compatible with mouse, keyboard and **touch** (mobile) to trigger hover
- Multi-language support, cross-platform support (Windows, macOS, Linux)

## Showcases

![render](render.gif)

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

Or, personalize the configuration:

```yaml
plugins:
  - document-dates:
      position: top            # Display position: top (after title)  bottom (end of document), default: bottom
      type: date               # Date type: date  datetime  timeago, default: date
      locale: en               # Localization: zh zh_tw en es fr de ar ja ko ru, default: en
      date_format: '%Y-%m-%d'  # Date format, Supports all Python datetime format strings, e.g., %Y-%m-%d, %b %d, %Y, etc
      time_format: '%H:%M:%S'  # Time format (valid only if type=datetime)
      exclude:                 # List of excluded files
        - temp.md              # Exclude specific file
        - private/*            # Exclude all files in private directory, including subdirectories
        - drafts/*.md          # Exclude all markdown files in the current directory drafts, but not subdirectories
      
      show_author: true        # Whether to display author: true false, default: true

```

## Specify time manually

The plugin will automatically get the exact time of the document, will automatically cache the creation time, but of course, you can also specify it manually in `Front Matter`

Priority: `Front Matter` > `Cache Files` > `File System Timestamps`

```yaml
---
created: 2023-01-01
modified: 2025-02-23
---

# Document Title
```

- `created` can be replaced with: `created, date, creation_date, created_at, date_created`
- `modified` can be replaced with: `modified, updated, last_modified, updated_at, last_update`

## Specify author manually

The plugin will automatically get the author of the document, will parse the email and make a link, also you can specify it manually in `Front Matter`

Priority: `Front Matter` > `Git Author Info` > `PC Username`

```yaml
---
author: any-name
email: e-name@gmail.com
---

# Document Title
```

- `author` can be replaced with: `author, name`
- `email` can be replaced with: `email, mail`

## Customization

The plugin supports deep customization, such as icon style, font style, theme color, animation type, dividing line, etc. All of it can be customized by modifying the code in the corresponding file (I've already written the code and comments, you just need to turn on the switch and change the value, it's super easy):

- Style & Theme: `docs/assets/document_dates/user.config.css`
- Properties & Animations: `docs/assets/document_dates/user.config.js`
- Localized languages: `docs/assets/document_dates/languages/` , refer to the template file `en.json` for any additions or modifications

Note: Due to the redesign of the configuration file update mechanism, the configuration file starting with document-dates.config in the previous version has been canceled and replaced by user.config

## Other Tips

- In order to get the exact creation time, a separate cache file is used to store the creation time of the file, located in the doc folder (hidden by default), please don't delete it:
    - `docs/.dates_cache.jsonl`, cache file (.json without the l is the old cache file and will be automatically migrated to .jsonl after any git commit)
    - `docs/.gitattributes`, configuration file (merge mechanism for cache file in case of multi-person collaboration)
- The Git Hooks mechanism is used to automatically trigger the storing of the cache (every time executes a git commit), and the cached file is automatically committed along with it
- The installation of Git Hooks is automatically triggered when the plugin is installed
- The above actions are fully automated without any manual intervention, applicable to any environment, and have been tested and validated in Git-less environments, CI/CD environments (e.g., GitHub Actions), one-person collaborations, multi-person collaborations, etc

## Development Stories (Optional)