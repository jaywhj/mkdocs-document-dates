# CHANGELOG



## v3.6.1 (2026-02-12)

### en

- File exclusion pattern support unix shell-style wildcards, such as `*` , `?` , `[]` etc
- Add hover effects for cover
- Optimize the style of recently updated list

### zh

- 文件排除模式支持 unix shell 风格的通配符，如 `*` , `?` , `[]` 等
- 为封面添加悬停效果
- 优化最近更新列表的样式



## v3.6 (2026-01-25)

### en

- New: The article list supports the summary mode and automatically extracts article summaries
- New: Reconstructed the UI layout of the recently updated document list; added multiple view modes including list, detail and grid, which support dynamic switching

### zh

- 新增：文章列表支持摘要模式，自动提取文章摘要
- 新增：重构最近更新的文档列表 UI 布局，新增列表、详情、网格等多种视图模式，可动态切换



## v3.5.2 (2025-12-26)

### en

- **New**: The plugin’s display structure can be freely configured in the front matter. See [Configuration Structure and Style](https://jaywhj.netlify.app/document-dates-en#Structure-and-Style)
- **New**: Added adaptive dynamic layout for the author list, which displays an optimal layout in real time to enhance user experience
- **New**: Enabled horizontal scrolling via mouse wheel for the author list to enhance user experience
- **New**: Implemented multi-source dynamic loading for author avatars, which can automatically match users’ network avatars
- **Fixed**: Optimized the loading sequence of plugin components to improve performance

### zh

- 新增：可在 front matter 中自由配置插件的显示结构，具体见：[配置结构与样式](https://jaywhj.netlify.app/document-dates-zh#%E7%BB%93%E6%9E%84%E4%B8%8E%E6%A0%B7%E5%BC%8F)
- 新增：为作者列表添加自适应动态布局，实时显示合理布局，优化体验
- 新增：为作者列表启用滚轮横向滚动，优化体验
- 新增：作者头像采用多源动态加载，能自动匹配用户网络头像
- 修复：优化插件组件的加载顺序，优化性能



## v3.5.1

### en

- Redesigned the UI presentation and hierarchical structure of the plugin for better compatibility, rationality, and user-friendliness
- Redesigned the Git avatar loading mechanism, which automatically fetches user avatars from Gravatar or WeAvatar
- Updated all sample templates for plugin rendering that can be used to customize the plugin. See [source-file.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/source-file.html)
- Added samples for tooltip z-index control
- Updated the sample template for loading the recently updated module in the sidebar. See [nav.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/nav.html)

### zh

- 重新设计插件的 UI 呈现方式和层级结构，更兼容，更合理，更人性化
- 重新设计 Git 头像的加载方式，自动从 gravatar 或 weavatar 加载用户头像
- 更新插件渲染的全部示例模板，可用来定制插件，参考 [source-file.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/source-file.html)
- 补充 tooltip 层级控制的示例
- 更新在侧边栏加载最近更新模块的示例模板，参考 [nav.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/nav.html)



## v3.5

### en

- Add configuration items `show_created` and `show_updated` to control whether to show dates
- Add compatibility for recently updated modules, compatible with all kinds of navigation plug-ins, will automatically load the correct title of the document
- Field update:
    | Old field:              | New field:             |
    | ----------------------- | ---------------------- |
    | document_dates_modified | document_dates_updated |
    | doc_modified            | doc_updated            |
    | modified_time           | updated_time           |
    | modified_field_names    | updated_field_names    |

### zh

- 添加配置项 `show_created` 和 `show_updated`，以控制是否显示日期
- 为最近更新的模块添加兼容性，兼容各种导航插件，会自动加载正确的文档标题
- 字段更新：
    | 旧字段：                 | 新字段：                |
    | ----------------------- | ---------------------- |
    | document_dates_modified | document_dates_updated |
    | doc_modified            | doc_updated            |
    | modified_time           | updated_time           |
    | modified_field_names    | updated_field_names    |



## v3.4.8

### en

- Optimize avatar path configuration to support local file paths
- Optimize the timing of obtaining values for template variables

### zh

- 优化头像路径配置以支持本地文件路径
- 优化模板变量的取值时机



## v3.4.7

### en

- Enhanced author configuration, now you can configure full information for all types of authors to enrich the user experience, see [Enhanced-author-configuration](https://jaywhj.netlify.app/document-dates-en#Enhanced-author-configuration) for details

### zh

- 增强作者配置，现在你可为所有类型的作者配置完整信息，丰富用户体验，详情见文档 [增强作者配置](https://jaywhj.netlify.app/document-dates-zh#增强作者配置)



## v3.4.6

### en

- Optimize user experience, when the URL avatar fails to load (no network/wrong URL/loading error), it will automatically switch to the character avatar

### zh

- 优化用户体验，URL头像加载失败时（无网/URL错误/加载错误），会自动切换到字符头像



## v3.4.5

### en

- New: Add the recently updated module anywhere in any md document using a line of code, see the documentation for [details](https://jaywhj.netlify.app/document-dates-en#Add-Recently-Updated-Module)
- New: Git author support aggregation, i.e. different email accounts of the same person can be shown as the same author
- Improved compatibility in Docker containers
- Optimize the selection logic for the last update time, see the documentation for [process](https://jaywhj.netlify.app/document-dates-en#Specify-Datetime) (this tweak ensures that the correct timestamp is read even if the file has been rebuilt via git checkout, git clone, etc.)

### zh

- 新增：在任意文档的任意位置使用一行代码添加最近更新模块，[详情](https://jaywhj.netlify.app/document-dates-zh#%E6%B7%BB%E5%8A%A0%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0%E6%A8%A1%E5%9D%97)见文档
- 新增：Git 作者支持聚合，即同一个人的不同邮箱账户可显示为同一作者
- 改进在 Docker 容器中的兼容性
- 优化了最后更新时间的择取逻辑，[流程](https://jaywhj.netlify.app/document-dates-zh#%E6%8C%87%E5%AE%9A%E6%97%A5%E6%9C%9F%E6%97%B6%E9%97%B4)见文档（这一调整可确保即使文件在通过 git checkout、git clone 等方式重建后，仍能读取正确的时间戳）



## v3.4.1

### en

- `show_author` adds text mode, now supports `true(avatar mode), text(text mode), false(hidden)`
- Optimize the loading logic of static resources
- Build and Package Adaptation PEP 517 Standard
- Updating document usage descriptions

### zh

- `show_author` 增加了文本模式，现在支持 `true(头像模式), text(文本模式), false(隐藏)`
- 优化静态资源的加载逻辑
- 构建与打包适配 PEP 517 标准
- 更新文档使用描述



## v3.4

### en

- New feature: Display the list of recently updated docs, see README.md for the example
- Added the recently updated data API, and now you can get the recently updated data use `config.extra.recently_updated_docs` in any template
- Extended a new plugin [mkdocs-recently-updated-docs](https://github.com/jaywhj/mkdocs-recently-updated-docs), you can add the recently updated module anywhere in any md document using a line of code `<!-- RECENTLY_UPDATED_DOCS -->` , which is also based on the data capabilities provided by this plugin and provides more template examples
- Localization adds support for Dutch and Português

### zh

- 新增显示最近更新的文档列表功能，使用示例见 README_zh.md
- 新增最近更新的文档数据接口，现在可以在任意模板中通过 `config.extra.recently_updated_docs` 获取最近更新的文档数据
- 扩展了新插件 [mkdocs-recently-updated-docs](https://github.com/jaywhj/mkdocs-recently-updated-docs)，可在任意md文档的任意位置使用一行代码 `<!-- RECENTLY_UPDATED_DOCS -->` 添加最近更新模块，也是基于此插件提供的数据能力，并提供了更多的模板示例
- 本地化增加 `nl pt` 的支持



## v3.3.3

### en

- Adjust `locale` to automatic mode, intelligently recognize user languages, and dynamically adapt to their localized languages without manual assignment
- The icon supports offline mode
- Adjust the selection policy for the creation time when caching
- Optimize multi-language customization and make configuration super easy, see [user.config.js](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js)
- Optimize other custom configuration options for easier use, see [user.config.js](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js) 
- Updated template usage examples, see [source-file.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/source-file.html)

### zh

- 调整 locale 为自动模式，智能识别用户语种，动态适配其本地化语言，无需手动指定（配置项保留）
- 图标支持离线模式
- 调整缓存时创建时间的择取策略
- 优化多语言自定义方式，配置超简单，具体见 [user.config.js](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js) 
- 优化其他自定义配置选项，使用更简单，具体见 [user.config.js](https://github.com/jaywhj/mkdocs-document-dates/blob/main/mkdocs_document_dates/static/config/user.config.js)  
- 更新了模板使用示例，具体见 [source-file.html](https://github.com/jaywhj/mkdocs-document-dates/blob/main/templates/overrides/partials/source-file.html)



## v3.3

### en

1. Support for avatar mode (Custom Avatar ` > ` GitHub Avatar ` > ` Character Avatar)
    - Character avatar: will be automatically generated based on the author's name with the following rules
        - Extract initials: English takes the combination of initials, other languages take the first character
        - Dynamic background color: Generate HSL color based on the hash of the name
    - GitHub avatar: will be automatically loaded by parsing the `repo_url` property in mkdocs.yml
    - Custom avatar: can be customized by customizing the author's `avatar` field in Front Matter
        - See the `README.md` for details
2. Adjusts the default value of `position` to `top` 
3. Support with template customization plugin, you have full control over the rendering logic and the plugin is only responsible for providing the data


### zh

1. 支持头像模式（自定义头像 > github头像 > 字符头像）
    - 字符头像：会根据作者姓名自动生成，规则如下
        - 提取 initials：英文取首字母组合，中文取首字
        - 动态背景色：基于名字哈希值生成 HSL 颜色
    - GitHub头像：会解析 mkdocs.yml 中的 `repo_url` 属性自动加载
    - 自定义头像：可在 Front Matter 中通过自定义作者的 `avatar` 字段进行自定义
        - 详情请查看 `README_zh.md` 
2. 调整 position 默认值为 top
3. 支持用模板自定义插件，你可以完全掌控渲染逻辑，插件只负责提供数据



## v3.2.1

### en

- Extremely optimized build efficiency - O(1), typically less than 0.2 seconds, regardless of whether the number of documents is 1,000 or 10,000
- Fix style alignment issue when 'position' is top
- Compatible with Material's instant-load property `navigation.instant`

### zh

- 极致优化构建速度，现在无论文档数量是1000还是10000，通常不到0.2秒
- 修复 position 为 top 时，样式对齐的问题
- 兼容 Material 主题的即时加载属性 `navigation.instant`