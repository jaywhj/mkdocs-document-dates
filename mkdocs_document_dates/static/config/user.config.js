/*
Part 1: 
    Configuration Overrides for Tooltip
    see: https://atomiks.github.io/tippyjs/
*/

/* Configure one by one: */
// tooltip_config.theme.light = 'tomato';
// tooltip_config.placement = 'top';
// tooltip_config.arrow = false;

/* Or, override all configuration items: */
/*
TooltipConfig.setConfig({
    theme: {
        // configurable: light material, or custom theme in user.config.css, for example: sorrel sublime tomato
        light: 'light',
        dark: 'material'
    },
    placement: 'bottom',    // placement: top bottom left right auto
    offset: [0, 10],         // placement offset: [horizontal, vertical]
    interactive: true,      // content in Tooltip is interactive
    allowHTML: true,        // whether to allow HTML in the tooltip content
    animation: 'scale',     // animation type: scale shift-away
    inertia: true,          // animation inertia
    // arrow: false,           // whether to allow arrows
    // animateFill: true,      // determines if the background fill color should be animated
    // delay: [400, null],     // delay: [show, hide], show delay is 400ms, hide delay is the default
});
*/

/* 
    Hook System of Tooltip
    The hook system allows you to execute custom logic at specific times, 
    such as adding custom interactions before the tooltip initialization and after initialization.
*/

/*
TooltipConfig.registerHook('beforeInit', async (context) => {
});
TooltipConfig.registerHook('afterInit', async (context) => {
});
*/



/*
Part 2: 
    Demonstrates how to register a local language when using 'timeago.js'
    Simply translate the English in parentheses into your own language, nothing else needs to be changed!
*/
/*
const localeFunc = (number, index) => {
    return [
        ['just now', 'right now'],
        ['%s seconds ago', 'in %s seconds'],
        ['1 minute ago', 'in 1 minute'],
        ['%s minutes ago', 'in %s minutes'],
        ['1 hour ago', 'in 1 hour'],
        ['%s hours ago', 'in %s hours'],
        ['1 day ago', 'in 1 day'],
        ['%s days ago', 'in %s days'],
        ['1 week ago', 'in 1 week'],
        ['%s weeks ago', 'in %s weeks'],
        ['1 month ago', 'in 1 month'],
        ['%s months ago', 'in %s months'],
        ['1 year ago', 'in 1 year'],
        ['%s years ago', 'in %s years']
    ][index];
};
const localeStr = 'whatever';
timeago.register(localeStr, localeFunc);
function formatTimeagoElements() {
    if (typeof timeago !== 'undefined') {
        document.querySelectorAll('.document-dates-plugin time').forEach(timeElement => {
            timeElement.textContent = timeago.format(timeElement.getAttribute('datetime'), localeStr);
        });
    }
}
// Refresh rendering after registration
if (typeof window.document$ !== 'undefined' && !window.document$.isStopped) {
    window.document$.subscribe(formatTimeagoElements);
} else {
    formatTimeagoElements();
}
*/



/*
Part 3: 
    Demonstrates how to register the local language for the plugin's tooltip,
        when the local language is missing, or when the default language translation is inaccurate.
    Simply translate the English in parentheses into your own language, nothing else needs to be changed!
*/
/*
// Way 1: User-defined one language
TooltipLanguage.registerUser('en', {
    created_time: "Custom Created",
    modified_time: "Custom Last Update",
    author: "Custom Author",
    authors: "Custom Authors"
});

// Way 2: User-defined multiple languages
const userLanguages = {
    en: {
        created_time: "Created",
        modified_time: "Last Update",
        author: "Author",
        authors: "Authors"
    },
    zh: {
        created_time: "创建时间",
        modified_time: "最后更新",
        author: "作者",
        authors: "作者"
    }
};
Object.entries(userLanguages).forEach(([locale, data]) => {
    TooltipLanguage.registerUser(locale, data);
});

// Refresh rendering after registration
if (typeof window.document$ !== 'undefined' && !window.document$.isStopped) {
    window.document$.subscribe(renderDocumentDates);
} else {
    renderDocumentDates();
}
*/