const { exec } = require('child_process');

function buildPython() {
    exec("python3 ./build.py")
}

function createTitle(identifier) {
    const words = [];
    for (const word of identifier.replaceAll("_", " ").split(" ")) {
        words.push(word[0].toUpperCase() + word.substr(1).toLowerCase());
    }
    return words.join(" ");
}

const variablePattern = new RegExp("\{\{([a-z0-9_-]+)\}\}", "ig");
const variables = {
    APP_NAME: process.env.npm_package_name,
    APP_TITLE: createTitle(process.env.npm_package_name),
};
function resolveVariable(_match, identifier) {
    const result = variables[identifier];
    if (result) {
        return result;
    } else {
        return "";
    }
}

/** @type {import('vite').UserConfig} */
export default {
    base: "./",
    build: {
        modulePreload: {
            polyfill: false,
        },
        commonjsOptions: {
            transformMixedEsModules: true,
        },
        minify: true,
        sourcemap: true,
        target: "ES2022",
    },
    plugins: [
        {
            name: 'prebuild-commands',
            handleHotUpdate: ({file, server}) => {
                if (file.endsWith(".py")) {
                    buildPython();
                    server.ws.send({
                        type: 'full-reload',
                        path: '*'
                    });
                }
            },
            buildStart: buildPython,
            transform(code, id) {
                if (id.endsWith('.ts') || id.endsWith('.html')) {
                    return {
                        code: code.replaceAll(variablePattern, resolveVariable),
                        map: null,
                    };
                } else {
                    return null;
                }
            },
            transformIndexHtml(htmlData, _ctx) {
                return htmlData.replaceAll(variablePattern, resolveVariable);
            }
        },
    ]
}
