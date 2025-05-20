# mkdocs-document-dates

English | [简体中文](README_zh.md)



A MkDocs plugin for displaying the <mark>exact</mark> creation and last modification dates of markdown document.

## Features

- **No Git dependency**, uses filesystem timestamps directly
- Supports manual date specification in `Front Matter`
- Support for multiple time formats (date, datetime, timeago)
- Support for document exclusion mode
- Flexible display position (top or bottom)
- Material style icons, elegant styling (Customizable)
- Supports Tooltip Hover Tips
  - Intelligent repositioning to always float optimally in view
  - Supports automatic theme switching following Material's light/dark color scheme
  - Support for customizing themes, styles, animations
  - Compatible with mouse, keyboard and **touch** (mobile) to trigger hover
- Support for CI/CD build systems (e.g. Github Actions)
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

Or, customize the configuration:

```yaml
plugins:
  - document-dates:
      type: date               # Date type: date  datetime  timeago, default: date
      locale: en               # Localization: zh zh_tw en es fr de ar ja ko ru, default: en
      date_format: '%Y-%m-%d'  # Date format, Supports all Python datetime format strings, e.g., %Y-%m-%d, %b %d, %Y, etc
      time_format: '%H:%M:%S'  # Time format (valid only if type=datetime)
      position: bottom         # Display position: top (after title)  bottom (end of document), default: bottom
      exclude:                 # List of excluded files
        - temp.md              # Exclude specific file
        - private/*            # Exclude all files in private directory, including subdirectories
        - drafts/*.md          # Exclude all markdown files in the current directory drafts, but not subdirectories
```

## Manual Date Specification

You can also manually specify the date of a Markdown document in its `Front Matter` :

```yaml
---
created: 2023-01-01
modified: 2025-02-23
---

# Document Title
```

- `created` can be replaced with: `created, date, creation_date, created_at, date_created`
- `modified` can be replaced with: `modified, updated, last_modified, updated_at, date_modified, last_update`

## Customization

This plugin supports deep customization, just modify the code in the corresponding file:

- Style & Theme: `docs/assets/document_dates/document-dates.config.css`
- Properties & Animations: `docs/assets/document_dates/document-dates.config.js`

Tip: If you want to restore the default effect, just delete this file and rebuild your project

## Tips

- It still works when using CI/CD build systems (e.g. Github Actions), here's how it works:
    1. First, you can configure the workflow like this (penultimate line) in your `.github/workflows/ci.yml`:
    ```
    ...
    
        - run: pip install mkdocs-document-dates
        - run: mkdocs gh-deploy --force
    ```
    2. Then update your Markdown document in `docs` as normal
    3. After running git add and git commit, you will see the auto-generated cache file `.dates_cache.json` (hidden by default) in the `docs` folder
        - Make sure you have installed python3 ahead of time and set environment variables
    4. Finally, run git push, and you can see that the `.dates_cache.json` file also exists in the docs directory in the GitHub repository, which means success!
- Priority for datetime reads:
    - `Front Matter` > `Cache file` > `Filesystem timestamp`
- If you are using MkDocs on a Linux system, the modification time is used as the creation time because of system limitations. If you need the exact creation time, you can specify it manually in Front Matter