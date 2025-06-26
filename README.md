# mkdocs-document-dates

English | [简体中文](README_zh.md)



An easy-to-use, lightweight MkDocs plugin for displaying the <mark>exact</mark> creation time, last modification time and author info of markdown documents.

## Features

- Always display exact meta-info of the document for any environment (no-Git, Git, all CI/CD build systems, etc)
- Support for manually specifying time and author in `Front Matter`
- Support for multiple time formats (date, datetime, timeago)
- Flexible display position (top or bottom)
- Elegant styling (fully customizable)
- Supports Tooltip Hover Tips
  - Intelligent repositioning to always float optimally in view
  - Supports automatic theme switching following Material's light/dark color scheme
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
      locale: en               # Localization: en zh zh_TW es fr de ar ja ko ru, default: en
      date_format: '%Y-%m-%d'  # Date format strings, e.g., %Y-%m-%d, %b %d, %Y, etc
      time_format: '%H:%M:%S'  # Time format strings (valid only if type=datetime)
      exclude:                 # List of excluded files
        - temp.md              # Exclude specific file
        - private/*            # Exclude all files in private directory, including subdirectories
      show_author: true        # Show author or not, default: true
```

## Specify time manually

The plugin will automatically get the exact time of the document, will automatically cache the creation time, but of course, you can also specify it manually in `Front Matter`

Priority order: `Front Matter` > `Cache Files` > `File System Timestamps`

```yaml
---
created: 2023-01-01
modified: 2025-02-23
---

# Document Title
```

- `created` can be replaced with: `created, date, creation`
- `modified` can be replaced with: `modified, updated, last_modified, last_updated`

## Specify author manually

The plugin will automatically get the author of the document, will parse the email and make a link, also you can specify it manually in `Front Matter`

Priority order: `Front Matter` > `Git Author` > `site_author (mkdocs.yml)` > `PC Username`

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

The plugin supports deep customization, such as **icon style, font style, theme color, animation type, dividing line**, etc. Everything is customizable (I've already written the code, you just need to turn on the uncomment switch):

|        Function：        | Location：                               |
| :----------------------: | ---------------------------------------- |
|     **Style & Theme**     | `docs/assets/document_dates/user.config.css` |
| **Properties & Functions** | `docs/assets/document_dates/user.config.js` |
| **Localized languages** | `docs/assets/document_dates/languages/` <br />refer to the template file `en.json` for any additions or modifications |

**Tip**: when `type: timeago` is set, timeago.js is enabled to render dynamic time, `timeago.min.js` only contains English and Chinese by default, if you need to load other languages, you can configure it as below (choose one):

- In `user.config.js`, refer to [the demo commented out](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js) at the bottom, translate it into your local language
- In `mkdocs.yml`, add the following two lines to configure the full version of `timeago.full.min.js` to load all languages at once
    ```yaml
    extra_javascript:
      - assets/document_dates/core/timeago.full.min.js
      - assets/document_dates/core/timeago-load.js
    ```

**Demo Images**:

![01-default-w](mkdocs_document_dates/demo_images/01-default-w.png)
![02-change-icon](mkdocs_document_dates/demo_images/02-change-icon.png)
![02-change-icon-color](mkdocs_document_dates/demo_images/02-change-icon-color.png)
![04-default-pop-up](mkdocs_document_dates/demo_images/04-default-pop-up.png)
![05-change-theme](mkdocs_document_dates/demo_images/05-change-theme.png)

![06-change-theme](mkdocs_document_dates/demo_images/06-change-theme.png)
![08-pop-up-from-bottom](mkdocs_document_dates/demo_images/08-pop-up-from-bottom.png)

## Used in templates

You can access the meta-info of a document in a template using the following variables:

- page.meta.document_dates_created
- page.meta.document_dates_modified
- page.meta.document_dates_authors

For example like this:

```jinja2
<div><span>{{ page.meta.document_dates_created }}</span></div>
<div><span>{{ page.meta.document_dates_modified }}</span></div>
{% set authors = page.meta.document_dates_authors %}
{% if authors %}
<div>
    {% for author in authors %}
    {% if author.email %}<a href="mailto:{{ author.email }}">{{ author.name }}</a>
    {% else %}<span>{{ author.name }}</span>{% endif %}
    {% endfor %}
</div>
{% endif %}
```

**Full example**: set the correct lastmod for [sitemap.xml](https://github.com/jaywhj/mkdocs-document-dates/blob/main/sitemap.xml) so that search engines can better handle SEO and thus increase your site's exposure (override path: `docs/overrides/sitemap.xml`)

## Other Tips

- In order to always get the exact creation time, a separate cache file is used to store the creation time of the document, located in the docs folder (hidden by default), please don't remove it:
    - `docs/.dates_cache.jsonl`, cache file
    - `docs/.gitattributes`, merge mechanism for cache file
- The Git Hooks mechanism is used to automatically trigger the storing of the cache (on each git commit), and the cached file is automatically committed along with it, in addition, the installation of Git Hooks is automatically triggered when the plugin is installed, without any manual intervention!

<br />

## Development Stories (Optional)

A dispensable, insignificant little plug-in, friends who have time can take a look \^\_\^ 

- **Origin**:
    - Because [mkdocs-git-revision-date-localized-plugin](https://github.com/timvink/mkdocs-git-revision-date-localized-plugin), a great project. When I used it at the end of 2024, I found that I couldn't use it locally because my mkdocs documentation was not included in git management, I don't understand why not read the file system time, but to use the git time, and the filesystem time is exact, then raised an issue to the author, but didn't get a reply for about a week (the author had a reply later, nice guy, I guess he was busy at the time), and then I thought, there is nothing to do during the Chinese New Year, and now AI is so hot, why not with the help of the AI try it out for myself, it was born, born in February 2025
- **Iteration**:
    - After development, I understood why not use filesystem time, because files will be rebuilt when they go through git checkout or clone, resulting in the loss of original timestamp information. There are many solutions:
    - Method 1: Use the last git commit time as the last update time and the first git commit time as the creation time, mkdocs-git-revision-date-localized-plugin does this. (This way, there will be a margin of error and dependency on git)
    - Method 2: Cache the original time in advance, and then read the cache subsequently (The time is exact and no dependency on any environment). The cache can be in Front Matter of the source document or in a separate file, I chose the latter. Storing in Front Matter makes sense and is easier, but this will modify the source content of the document, although it doesn't have any impact on the body, but I still want to ensure the originality of the data!
- **Difficulty**:
    1. When to read and store original time? This is just a plugin for mkdocs, with very limited access and permissions, mkdocs provides only build and serve, so in case a user commits directly without executing build or serve (e.g., when using a CI/CD build system), then you won't be able to retrieve the time information of the file, not to mention caching it!
        - Let's take a straight shot: the Git Hooks mechanism was found, prompted by the AI, which can trigger a custom script when a specific git action occurs, such as every time commit is performed
    2. How to install Git Hooks automatically? When and how are they triggered? Installing packages from PyPI via pip doesn't have a standard post-install hook mechanism
        - Workaround: After analyzing the flow of pip installing packages from PyPI, I found that when compiling and installing through the source package (sdist), setuptools will be called to handle it, so we can find a way to implant the installation script in the process of setuptools, i.e., we can add a custom script in setup.py
    3. How to design a cross-platform hook? To execute a python script, we need to explicitly specify the python interpreter, and the user's python environment varies depending on the operating system, the way python is installed, and the configuration, so how can we ensure that it works properly in all environments?
        - Solution: I considered using a shell script, but since I'd have to call back to python eventually, it's easier to use a python script. We can detect the user's python environment when the hook is installed, and then dynamically set the hook's shebang line to set the correct python interpreter
    4. How can I ensure that a single cache file does not conflict when collaborating with multi-person?
        - Workaround: use JSONL (JSON Lines) instead of JSON, and with the merge strategy 'merge=union'
- **Improve**:
    - Since it's a newly developed plugin, it will be designed in the direction of **excellent products**, and the pursuit of the ultimate **ease of use, simplicity and personalization**
        - **Ease of use**: don't let users do things manually if you can, e.g., auto-install Git Hooks, auto-cache, auto-commit, provide customized templates, etc
        - **Simplicity**: no unnecessary configuration, no Git dependencies, no CI/CD configuration dependencies, no other package dependencies
        - **Personalization**: almost everything can be customized, whether it's icons, styles, themes, or features, it's all fully customizable
    - In addition, it has good compatibility and extensibility, and works well in WIN7, mobile devices, old Safari, etc
- **The Last Secret**:
    - Programming is a hobby, and I'm a marketer of 8 years (Feel free to leave a comment)