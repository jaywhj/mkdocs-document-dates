# mkdocs-document-dates

English | [简体中文](README_zh.md)



A MkDocs plugin for displaying <mark>accurate</mark> document creation and last modification dates.

## Features

- Automatically displays document creation and last modification times
- **No Git dependency**, uses filesystem timestamps directly
- Supports manual date specification in `Front Matter`
- Cross-platform support (Windows, macOS, Linux)
- Support for multiple time formats (date, datetime, timeago)
- Flexible display position (top or bottom)
- Support for customizing display styles (CSS)
- Support for document exclusion mode
- Material Design icons, Elegant styling
- Lightweight with no extra dependencies
- Multi-language support
- Support for CI/CD build systems (e.g. Github Actions)

## Installation

```bash
pip install mkdocs-document-dates
```

## Configuration

Just add the plugin to your mkdocs.yml:

```yaml
plugins:
  - document-dates
```

Or, customize the configuration:

```yaml
plugins:
  - document-dates:
      type: date               # Date type: date | datetime | timeago, default: date
      locale: en               # Localization: zh zh_tw en es fr de ar ja ko ru, default: en
      date_format: '%Y-%m-%d'  # Date format
      time_format: '%H:%M:%S'  # Time format (valid only if type=datetime)
      position: bottom         # Display position: top (after title) | bottom (end of document), default: bottom
      exclude:                 # List of file patterns to exclude
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

- `created` can be replaced by any of the following fields: `created, date, creation_date, created_at, date_created`
- `modified` can be replaced by any of the following fields: `modified, updated, last_modified, updated_at, date_modified, last_update`

## Custom Display Styles (CSS)

Simply modify the code in the file `docs/assets/document_dates.css`

## Configuration Options

- **type** : Date type (default: `date` )
  - `date` : Display date only
  - `datetime` : Display date and time
  - `timeago` : Display relative time (e.g., 2 minutes ago)
- **locale** : Localization (default: `en` )
  - Supports: `zh zh_tw en es fr de ar ja ko ru`
- **date_format** : Date format (default: `%Y-%m-%d`)
  - Supports all Python datetime format strings, e.g., %Y-%m-%d, %b %d, %Y, etc.
- **time_format** : Time format (default: `%H:%M:%S`)
- **position** : Display position (default: `bottom`)
  - `top` : Display after the first heading
  - `bottom` : Display at the end of the document
- **exclude** : File exclusion list (default: [] )
  - Supports glob patterns, e.g., ["private/\*", "temp.md", "drafts/\*.md"]

## Tips

- It still works when using CI/CD build systems (e.g. Github Actions), used a cache file `.dates_cache.json` to solve this problem:
    1. First, you can configure the workflow like this (penultimate line) in your .github/workflows/ci.yml:
    ```
    ...
    
        - run: pip install mkdocs-document-dates
        - run: mkdocs gh-deploy --force
    ```
    2. Then update your Markdown document in MkDocs as normal
    3. After running git add and git commit, you will see the auto-generated cache file .dates_cache.json (hidden by default) in the `docs` folder under MkDocs
        - Make sure you have installed python3 ahead of time and set environment variables
    4. Finally, run git push, and you can see that there are also .dates_cache.json files in the docs directory in the GitHub repository, which means success
- Priority of time reads:
    - `Front Matter` > `Cache file` > `Filesystem timestamp`
- If you are using MkDocs on a Linux system, the modification time is used as the creation time because of system limitations. If you need the exact creation time, you can specify it manually in Front Matter