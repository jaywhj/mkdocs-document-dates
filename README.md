# mkdocs-document-dates

English | [简体中文](README_zh.md)



A new generation MkDocs plugin for displaying exact **creation time, last update time, authors, email** of documents

## Features

- Always display **exact** meta-info of the document for any environment (no-Git, Git, all CI/CD build systems, etc)
- Support for manually specifying time and author in `Front Matter`
- Support for multiple time formats (date, datetime, timeago)
- Flexible display position (top or bottom)
- Elegant styling (fully customizable)
- Supports Tooltip Hover Tips
    - Intelligent dynamic positioning, always floating optimally in view
    - Supports automatic theme switching following Material's light/dark color scheme
- Multi-language support, localization support, intelligent recognition of user language, automatic adaptation
- Cross-platform support (Windows, macOS, Linux)
- **Ultimate build efficiency**: O(1), no need to set env vars to distinguish runs

| PK of Build Efficiency:     | 100 md: | 1000 md: | Time Complexity: |
| --------------------------- | :-----: | :------: | :----------: |
| git-revision-date-localized |  > 3 s   |  > 30 s   |    O(n)    |
| document-dates              | < 0.1 s  | < 0.15 s  |    O(1)    |


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
      position: top            # Display position: top (after title)  bottom (end of document)
      type: date               # Date type: date  datetime  timeago, default: date
      exclude:                 # List of excluded files
        - temp.md              # Exclude specific file
        - drafts/*             # Exclude all files in drafts folder, including subfolders
      date_format: '%Y-%m-%d'  # Date format strings, e.g., %Y-%m-%d, %b %d, %Y, etc
      time_format: '%H:%M:%S'  # Time format strings (valid only if type=datetime)
```

## Specify time manually

By default, the plugin will **automatically** get the exact time of the document, and will automatically cache the creation time, without manual intervention

- **Priority**: `Front Matter` > `File System Timestamps(Cached)` > `Git Timestamps`
- If you want to customize it, you can specify it manually in Front Matter:
    ```markdown
    ---
    created: 2023-01-01
    modified: 2025-02-23
    ---
    
    ```
- `created` can be replaced with: `created, date, creation`
- `modified` can be replaced with: `modified, updated, last_modified, last_updated`

## Configure Author

By default, the plugin will **automatically** get the author of the document, and will automatically parse the email and then do the link, without manual intervention

- **Priority**: `Front Matter` > `Git Author` > `site_author(mkdocs.yml)` > `PC Username`
- If you want to customize it, you can configure an author in Front Matter with the field `name`:
    ```markdown
    ---
    name: any-name
    email: e-name@gmail.com
    ---
    
    ```

## Configure Avatar

By default, the plugin will **automatically** loads the author avatar, without manual intervention

**Priority**: `Custom Avatar` > `GitHub Avatar` > `Character Avatar`

1. Character avatar: will be automatically generated based on the author's name with the following rules
    - Extract initials: English takes the combination of initials, other languages take the first character
    - Dynamic background color: Generate HSL color based on the hash of the name
2. GitHub avatar: will be automatically loaded by parsing the `repo_url` property in mkdocs.yml
3. Custom avatar: can be customized by customizing the author's `avatar` field in Front Matter
    ```markdown
    ---
    # Way 1: Configure a full author (fields optional)
    author:
        name: jay
        email: jay@qq.com
        avatar: https://xxx.author-avatar-URL.com/xxx.png
        url: https://xxx.website-URL.com/xxx
        description: author description
    
    # Way 2: Configure multiple authors
    authors:
        - jaywhj
        - dawang
        - sunny
    
    ---
    ```
- If you want to configure complete information for multiple authors, you can create a separate configuration file `authors.yml` in the `docs/` directory, see the [authors.yml](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/authors.yml) for its format
- If the URL avatar fails to load, it automatically falls back to the character avatar

## Customization

The plugin supports full customization, such as **icon style, theme color, font, animation, dividing line** etc, and the entrance has been preset, you just need to find the file below and uncomment it:

|        Category:        | Location:                               |
| :----------------------: | ---------------------------------------- |
|     **Style & Theme**     | `docs/assets/document_dates/user.config.css` |
| **Properties & Functions** | `docs/assets/document_dates/user.config.js` |

![customization](customization.gif)

## Localization

- **tooltip**: the plugin has 10 built-in languages: `en zh zh_TW es fr de ar ja ko ru`, **no need for manual configuration**, intelligent recognition, automatic switching
    - If the language is missing or the built-in language is inaccurate, you can refer to [Part 3](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js) in `user.config.js` to register and add it yourself, or submit an issue
    - The original configuration option `locale` is retained, but manual configuration is no longer recommended
- **timeago**: when `type: timeago` is set, timeago.js is enabled to render dynamic time, `timeago.min.js` only contains English and Chinese by default, if need to load other languages, you can configure it as below (choose one):
    - In `user.config.js`, refer to [Part 2](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js), register and add it yourself
    - In `mkdocs.yml`, configure the full version of `timeago.full.min.js` to reload all languages at once
        ```yaml
        extra_javascript:
        - assets/document_dates/core/timeago.full.min.js
        ```

## Template Variables

You can access the meta-info of a document in a template using the following variables:

- page.meta.document_dates_created
- page.meta.document_dates_modified
- page.meta.document_dates_authors

Usage examples:

- **Example 1**: Set the correct `lastmod` for your site's `sitemap.xml` so that search engines can better handle SEO and thus increase your site's exposure (download [sitemap.xml](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/sitemap.xml) and override this path: `docs/overrides/sitemap.xml`)
- **Example 2**: Using the template to re-customize the plugin, you have full control over the rendering logic and the plugin is only responsible for providing the data (download [source-file.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/source-file.html) and override this path: `docs/overrides/partials/source-file.html`)

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
        - Straight to the bottom line: Git Hooks can be used to trigger custom scripts when specific git actions occur, such as every time a commit occurs
    2. How to install Git Hooks automatically? When and how are they triggered? Installing packages from PyPI via pip doesn't have a standard post-install hook mechanism
        - Workaround: After analyzing the flow of pip installing packages from PyPI, I found that when compiling and installing through the source package (sdist), setuptools will be called to handle it, so we can find a way to implant the installation script in the process of setuptools, i.e., we can add a custom script in setup.py
    3. How to design a cross-platform hook? To execute a python script, we need to explicitly specify the python interpreter, and the user's python environment varies depending on the operating system, the way python is installed, and the configuration, so how can we ensure that it works properly in all environments?
        - Solution: I considered using a shell script, but since I'd have to call back to python eventually, it's easier to use a python script. We can detect the user's python environment when the hook is installed, and then dynamically set the hook's shebang line to set the correct python interpreter
    4. How can I ensure that a single cache file does not conflict when collaborating with multi-person?
        - Workaround: use JSONL (JSON Lines) instead of JSON, and with the merge strategy 'merge=union'
    5. How to reduce build time when there are a lot of documents ( >1000 )?  Getting git information about a document is usually a file I/O operation, and if there are a lot of files, the efficiency of the operation will plummet. 1,000 documents can be expected to take more than 30 seconds, which is intolerable to the user
        - Solution: Reduce the number of I/Os + Use caching + Replace less efficient system functions
- **Improve**:
    - Since it's a newly developed plugin, it will be designed in the direction of **excellent products**, and the pursuit of the ultimate **ease of use, simplicity, compatibility, personalization, intelligence**
        - **Ease of use**: there are no complex configurations, only 2-3 commonly used configuration options, in addition, a template is provided for personalized configurations
        - **Simplicity**: no unnecessary configuration, no Git dependencies, no CI/CD configuration dependencies, no other package dependencies
        - **Compatibility**: works well on older operating systems and browsers, such as WIN7, MacOS 10.11, iOS 12, Chrome 63.0.3239
        - **Personalization**: fully customizable and full control over the rendering logic, the plugin is only responsible for providing the data
        - **Intelligence**: intelligently parse document time, author, avatar, intelligent recognition of user language and automatic adaptation, in addition, there are auto-install Git Hooks, auto-cache, auto-commit
- **The Last Secret**:
    - Programming is a hobby, and I'm a marketer of 8 years (Feel free to leave a comment)