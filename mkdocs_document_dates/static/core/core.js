const defaultConfig = {
    // configurable: light material, or custom theme in user.config.css
    theme: {
        light: 'light',
        dark: 'material'
    },
    tooltip: {
        placement: 'bottom',    // placement: top bottom left right auto
        offset: [0, 10],        // placement offset: [horizontal, vertical]
        interactive: true,      // content in Tooltip is interactive
        allowHTML: true,        // whether to allow HTML in the tooltip content
        
        animation: 'scale',     // animation type: scale shift-away
        inertia: true,          // animation inertia
        // arrow: false,           // whether to allow arrows

        // animateFill: true,      // determines if the background fill color should be animated

        // delay: [400, null],     // delay: [show, hide], show delay is 400ms, hide delay is the default
    }
};

let config = { ...defaultConfig };


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

// Configuration API
function setConfig(newConfig) {
    config = {
        ...defaultConfig,
        ...newConfig
    };
}

// Theme management
function getCurrentTheme() {
    const scheme = (document.body && document.body.getAttribute('data-md-color-scheme')) || 'default';
    return scheme === 'slate' ? config.theme.dark : config.theme.light;
}

// Main initialization
async function init() {
    await executeHooks('beforeInit', { config });

    // Configure the properties of the Tooltip here, available documents: https://atomiks.github.io/tippyjs/
    const tippyInstances = tippy('[data-tippy-content]', {
        ...config.tooltip,
        theme: getCurrentTheme()    // Initialize Tooltip's theme based on Material's light/dark color scheme
    });

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

    await executeHooks('afterInit', { tippyInstances, observer });
    return { tippyInstances, observer };
}



const INSTANCE_KEY = Symbol('DocumentDatesInstance');

class InitManager {
    constructor() {
        this.initPromise = null;
    }

    getInstance() {
        if (window[INSTANCE_KEY]) {
            return Promise.resolve(window[INSTANCE_KEY]);
        }
        return this.initialize();
    }

    initialize() {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = init().then(instance => {
            window[INSTANCE_KEY] = instance;
            return instance;
        });

        return this.initPromise;
    }
}

const initManager = new InitManager();

function setupInitializationTrigger() {
    function checkAndInit() {
        if (document.querySelector('[data-tippy-content]')) {
            initManager.getInstance();
            return true;
        }
        return false;
    }

    if (document.readyState !== 'loading') {
        if (checkAndInit()) return;
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (checkAndInit()) return;

        const observer = new MutationObserver((mutations) => {
            if (checkAndInit()) {
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-tippy-content']
        });
    });
}

setupInitializationTrigger();



// Export API
window.DocumentDates = {
    init: () => initManager.getInstance(),
    registerHook,
    setConfig
};
