# mkdocs-document-dates

English | [简体中文](README_zh.md)



A MkDocs plugin for displaying **accurate** document creation and last modification dates.

## Features

- Automatically displays document creation and last modification times
- No Git dependency, uses filesystem timestamps directly
- Supports manual date specification in `Front Matter`
- Cross-platform support (Windows, macOS, Linux)
- Configurable time display formats (supports date, time, and relative time)
- Flexible display position (top or bottom)
- File exclusion rules support
- Material Design icons, Elegant styling
- Lightweight with no extra dependencies
- Multi-language support

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
      time_format: '%H:%M:%S'  # Time format
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
created_date: 2023-01-01
modified_date: 2023-12-31
---

# Document Title
```



## Configuration Options

- `type` : Date type (default: `date` )
  - `date` : Display date only
  - `datetime` : Display date and time
  - `timeago` : Display relative time (e.g., 2 minutes ago)
- `locale` : Localization (default: `en` )
  - Supports: `zh zh_tw en es fr de ar ja ko ru`
- `date_format` : Date format (default: `%Y-%m-%d`)
  - Supports all Python datetime format strings, e.g., %Y-%m-%d, %b %d, %Y, etc.
- `time_format` : Time format (default: `%H:%M:%S`)
- `position` : Display position (default: `bottom`)
  - `top` : Display after the first heading
  - `bottom` : Display at the end of the document
- `exclude` : File exclusion list (default: [] )
  - Supports glob patterns, e.g., ["private/\*", "temp.md", "drafts/\*.md"]

## Notes

- Creation time behavior varies across operating systems:
  - Windows: Uses file creation time
  - macOS: Uses file creation time (birthtime)
  - Linux: Uses modification time as creation time due to system limitations
- For accurate creation times, it's recommended to specify dates manually in Front Matter

