/*
    Part 1: Tooltip 配置
*/
const ttDefaultConfig = {
    // 可配置: light material, 或在 user.config.css 中自定义的主题
    theme: {
        light: 'light',
        dark: 'material'
    },
    placement: 'bottom',    // placement: top bottom left right auto
    offset: [0, 12],        // placement offset: [horizontal, vertical]
    interactive: true,      // content in Tooltip is interactive
    allowHTML: true,        // whether to allow HTML in the tooltip content
    animation: 'scale',     // animation type: scale shift-away
    inertia: true,          // animation inertia
    // arrow: false,           // whether to allow arrows
    // animateFill: true,      // determines if the background fill color should be animated
    // delay: [400, null],     // delay: [show, hide], show delay is 400ms, hide delay is the default
};
let tooltip_config = { ...ttDefaultConfig };
function setConfig(newConfig) {
    tooltip_config = {
        ...ttDefaultConfig,
        ...newConfig
    };
}
window.TooltipConfig = { setConfig };


function getCurrentTheme() {
    // 基于 Material's light/dark 配色方案返回对应的 Tooltip 主题
    const scheme = (document.body && document.body.getAttribute('data-md-color-scheme')) || 'default';
    return scheme === 'slate' ? tooltip_config.theme.dark : tooltip_config.theme.light;
}

async function initTippy() {
    // 创建上下文对象，将其传递给钩子并从函数中返回
    const context = { tooltip_config };

    // 初始化 tippy 实例
    const tippyInstances = tippy('[data-tippy-content]', {
        ...tooltip_config,
        theme: getCurrentTheme()
    });
    context.tippyInstances = tippyInstances;

    // 添加观察者，监控 Material's 配色变化，自动切换 Tooltip 主题
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
    context.observer = observer;

    // 返回包含 tippyInstances 和 observer 的上下文，用于后续清理
    return context;
}

// 通过 IIFE（立即执行的函数表达式）创建 tippyManager
const tippyManager = (() => {
    let tippyInstances = [];
    let observer = null;
    function cleanup() {
        // 销毁之前的 tippy 实例
        if (tippyInstances.length > 0) {
            tippyInstances.forEach(instance => instance.destroy());
            tippyInstances = [];
        }
        // 断开之前的观察者连接
        if (observer) {
            observer.disconnect();
            observer = null;
        }
    }
    return {
        // 每一次调用都生成新的实例（兼容 navigation.instant）
        initialize() {
            // 先清理以前的实例
            cleanup();
            // 初始化新实例
            initTippy().then(context => {
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
// 通过 IIFE（立即执行的函数表达式）创建 TooltipLanguage
window.TooltipLanguage = (function () {
    const allLangs = new Map();

    /*
    用户 locale 值      匹配顺序（fallback 列表）
    zh-Hans-CN         zh-Hans-CN → zh-Hans → zh → en
    zh_CN              zh-CN → zh → en
    fr-FR              fr-FR → fr → en
    ko                 ko → en
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
        register(locale, data) {
            // 合并数据，支持增量更新
            const existingData = allLangs.get(locale) || {};
            allLangs.set(locale, {
                ...existingData,
                ...data
            });
        },
        get(locale) {
            // 优先原值直接匹配
            if (allLangs.has(locale)) return allLangs.get(locale);
            // 进入降级匹配
            const fallbacks = generateFallbacks(locale);
            for (const fallbackLocale of fallbacks) {
                const data = allLangs.get(fallbackLocale);
                if (data) {
                    return data;
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
    TooltipLanguage.register(locale, data);
});

function resolveTimeagoLocale(rawLocale) {
    // 兼容 「ISO 639、ISO 3166、BCP 47」 格式
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

// 主逻辑（初始化目的，缺更新函数）
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
        tippyManager.initialize();
    });
} else {
    renderDocumentDates();
    generateAvatar();
    document.addEventListener('DOMContentLoaded', tippyManager.initialize);
}