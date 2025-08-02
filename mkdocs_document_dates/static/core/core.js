/*
    Part 1: Tooltip 配置
*/
const defaultConfig = {
    // 可配置: light material, 或在 user.config.css 中自定义的主题
    theme: {
        light: 'light',
        dark: 'material'
    },
    tooltip: {
        placement: 'bottom',    // placement: top bottom left right auto
        offset: [0, 12],        // placement offset: [horizontal, vertical]
        interactive: true,      // content in Tooltip is interactive
        allowHTML: true,        // whether to allow HTML in the tooltip content
        animation: 'scale',     // animation type: scale shift-away
        inertia: true,          // animation inertia
        // arrow: false,           // whether to allow arrows
        // animateFill: true,      // determines if the background fill color should be animated
        // delay: [400, null],     // delay: [show, hide], show delay is 400ms, hide delay is the default
    }
};

let tooltip_config = { ...defaultConfig };

// Configuration API
function setConfig(newConfig) {
    tooltip_config = {
        ...defaultConfig,
        ...newConfig
    };
}

// Hook System
const hooks = {
    beforeInit: [],
    afterInit: []
};

// Hook registration API
function registerHook(hookName, callback) {
    if (hooks[hookName]) {
        hooks[hookName].push(callback);
    }
}

// Hook execution
async function executeHooks(hookName, context) {
    if (hooks[hookName]) {
        for (const hook of hooks[hookName]) {
            await hook(context);
        }
    }
}

// Export API
window.TooltipConfig = {
    registerHook,
    setConfig
};

// Theme management
function getCurrentTheme() {
    const scheme = (document.body && document.body.getAttribute('data-md-color-scheme')) || 'default';
    return scheme === 'slate' ? tooltip_config.theme.dark : tooltip_config.theme.light;
}

// Main initialization
async function init() {
    // Create context object to pass to hooks and return from function
    const context = { tooltip_config };

    // Execute beforeInit hooks
    await executeHooks('beforeInit', context);

    // Configure the properties of the Tooltip here, available documents: https://atomiks.github.io/tippyjs/
    const tippyInstances = tippy('[data-tippy-content]', {
        ...tooltip_config.tooltip,
        theme: getCurrentTheme()    // Initialize Tooltip's theme based on Material's light/dark color scheme
    });

    // Store instances in context
    context.tippyInstances = tippyInstances;

    // Automatic theme switching. Set Tooltip's theme to change automatically with the Material's light/dark color scheme
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(async (mutation) => {
            if (mutation.attributeName === 'data-md-color-scheme') {
                const newTheme = getCurrentTheme();
                tippyInstances.forEach(instance => {
                    instance.setProps({ theme: newTheme });
                });
            }
        });
    });

    observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['data-md-color-scheme']
    });

    // Store observer in context
    context.observer = observer;

    // Execute afterInit hooks
    await executeHooks('afterInit', context);

    // Return context with instances and observer for cleanup
    return context;
}

// Initialization Manager
const initManager = (() => {
    let tippyInstances = [];
    let observer = null;

    // Function to clean up previous instances
    function cleanup() {
        // Destroy previous tippy instances if they exist
        if (tippyInstances.length > 0) {
            tippyInstances.forEach(instance => instance.destroy());
            tippyInstances = [];
        }

        // Disconnect previous observer if it exists
        if (observer) {
            observer.disconnect();
            observer = null;
        }
    }

    return {
        // This can be called multiple times, especially with navigation.instant
        loadTippyInstances() {
            // Clean up previous instances first
            cleanup();

            // Initialize new instances
            init().then(context => {
                if (context && context.tippyInstances) {
                    tippyInstances = context.tippyInstances;
                }
                if (context && context.observer) {
                    observer = context.observer;
                }
            });
        }
    };
})();



/*
    Part 2: 自动生成字符头像
*/
function isLatin(name) {
    return /^[A-Za-z\s]+$/.test(name.trim());
}
function extractInitials(name) {
    name = name.trim();
    if (!name) return '?';
    if (isLatin(name)) {
        const parts = name.toUpperCase().split(/\s+/).filter(Boolean);
        return parts.length >= 2 ? parts[0][0] + parts[parts.length - 1][0] : parts[0][0];
    } else {
        return name[0];
    }
}
function nameToHSL(name, s = 50, l = 55) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, ${s}%, ${l}%)`;
}
function generateAvatar() {
    document.querySelectorAll('.avatar-wrapper').forEach(wrapper => {
        const name = wrapper.dataset.name || '';
        const initials = extractInitials(name);
        const bgColor = nameToHSL(name);

        const textEl = wrapper.querySelector('.avatar-text');
        textEl.textContent = initials;
        textEl.style.backgroundColor = bgColor;

        const imgEl = wrapper.querySelector('img.avatar');
        if (!imgEl) return;
        imgEl.onerror = () => {
            imgEl.style.display = 'none';
        };
    });
}



/*
    Part 3: locale 自动本地化，同时也支持用户自定义
*/
window.TooltipLanguage = (function () {
    const defaultLangs = new Map();
    const userLangs = new Map();

    /*
    用户 locale 值      匹配顺序（fallback 列表）              实际使用的配置
    zh-Hans-CN         zh-hans-cn → zh-hans → zh → en       zh
    zh_CN              zh-cn → zh → en                      zh
    fr-FR              fr-fr → fr → en                      fr
    ko                 ko → en                              fallback to en if ko not found
    */
    // 生成 fallback 列表
    function generateFallbacks(locale, defaultLocale = 'en') {
        const normalized = locale.trim().replace(/_/g, '-');
        const parts = normalized.split('-');
        const fallbacks = [];
        for (let i = parts.length - 1; i >= 2; i--) {
            fallbacks.push(parts.slice(0, i).join('-'));
        }
        fallbacks.push(parts[0]);
        if (!fallbacks.includes(defaultLocale)) {
            fallbacks.push(defaultLocale);
        }
        return fallbacks;
    }
    return {
        registerDefault(locale, data) {
            defaultLangs.set(locale, data);
        },
        registerUser(locale, data) {
            userLangs.set(locale, data);
        },
        get(locale) {
            // 优先原值直接匹配，提高效率
            if (userLangs.has(locale)) return userLangs.get(locale);
            if (defaultLangs.has(locale)) return defaultLangs.get(locale);
            // 进入降级匹配
            const fallbacks = generateFallbacks(locale);
            for (const fallbackLocale of fallbacks) {
                const defaultData = defaultLangs.get(fallbackLocale);
                const userData = userLangs.get(fallbackLocale);
                if (defaultData || userData) {
                    return {
                        ...(defaultData || {}),
                        ...(userData || {})
                    };
                }
            }
            return {};
        }
    };
})();
// 默认语言包
const defaultLanguages = {
    ar: {
        created_time: "تاريخ الإنشاء",
        modified_time: "تاريخ التعديل",
        author: "المؤلف",
        authors: "المؤلفون"
    },
    de: {
        created_time: "Erstellungszeit",
        modified_time: "Änderungszeit",
        author: "Autor",
        authors: "Autoren"
    },
    en: {
        created_time: "Created",
        modified_time: "Last Update",
        author: "Author",
        authors: "Authors"
    },
    es: {
        created_time: "Fecha de creación",
        modified_time: "Fecha de modificación",
        author: "Autor",
        authors: "Autores"
    },
    fr: {
        created_time: "Date de création",
        modified_time: "Date de modification",
        author: "Auteur",
        authors: "Auteurs"
    },
    ja: {
        created_time: "作成日時",
        modified_time: "更新日時",
        author: "著者",
        authors: "著者"
    },
    ko: {
        created_time: "작성일",
        modified_time: "수정일",
        author: "작성자",
        authors: "작성자"
    },
    ru: {
        created_time: "Дата создания",
        modified_time: "Дата изменения",
        author: "Автор",
        authors: "Авторы"
    },
    zh: {
        created_time: "创建时间",
        modified_time: "最后更新",
        author: "作者",
        authors: "作者"
    },
    zh_TW: {
        created_time: "建立時間",
        modified_time: "修改時間",
        author: "作者",
        authors: "作者"
    }
}
// 统一注册所有默认语言
Object.entries(defaultLanguages).forEach(([locale, data]) => {
    TooltipLanguage.registerDefault(locale, data);
});

// 兼容 「ISO 639、ISO 3166、BCP 47」 格式
function resolveTimeagoLocale(rawLocale) {
    const shortLang = rawLocale.trim().replace(/-/g, '_').split('_')[0];
    const fixLocale = {
        bn: 'bn_IN',
        en: 'en_US',
        hi: 'hi_IN',
        id: 'id_ID',
        nb: 'nb_NO',
        nn: 'nn_NO',
        pt: 'pt_BR',
        zh: 'zh_CN'
    };
    return fixLocale[shortLang] || shortLang;
}

// 主逻辑
window.renderDocumentDates = function () {
    const plugins = document.querySelectorAll('.document-dates-plugin');
    if (!plugins.length) return;

    const iconKeyMap = {
        doc_created: 'created_time',
        doc_modified: 'modified_time',
        doc_author: 'author',
        doc_authors: 'authors'
    };

    plugins.forEach(ddPlugin => {
        // Step 1: 获取 locale
        const rawLocale =
            ddPlugin.getAttribute('locale') ||
            navigator.language ||
            navigator.userLanguage ||
            document.documentElement.lang ||
            'en';

        // Step 2: 处理 time 元素（使用 timeago 时）
        if (typeof timeago !== 'undefined') {
            const tLocale = resolveTimeagoLocale(rawLocale);
            ddPlugin.querySelectorAll('time').forEach(timeEl => {
                timeEl.textContent = timeago.format(timeEl.getAttribute('datetime'), tLocale);
            });
        }

        // Step 3: 加载 locale 对应的 tooltip 语言包
        const langData = TooltipLanguage.get(rawLocale);

        // Step 4: 处理 tooltip 内容
        ddPlugin.querySelectorAll('[data-tippy-content]').forEach(tippyEl => {
            const iconEl = tippyEl.querySelector('[data-icon]');
            const rawIconKey = iconEl ? iconEl.getAttribute('data-icon') : '';
            const iconKey = iconKeyMap[rawIconKey] || 'author';
            if (langData[iconKey]) {
                tippyEl.dataset.tippyContent = langData[iconKey] + ': ' + tippyEl.dataset.tippyRaw;
            }
        });
    });
};



/*
    入口: 兼容 Material 主题的 'navigation.instant' 属性
*/
if (typeof window.document$ !== 'undefined' && !window.document$.isStopped) {
    window.document$.subscribe(() => {
        renderDocumentDates();
        generateAvatar();
        initManager.loadTippyInstances();
    });
} else {
    renderDocumentDates();
    generateAvatar();
    document.addEventListener('DOMContentLoaded', initManager.loadTippyInstances);
}