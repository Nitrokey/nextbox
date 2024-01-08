"use strict";

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

const global = {
    '$': '19.0.0',
    Backbone: '18.0.0',
    Clipboard: '18.0.0',
    ClipboardJs: '18.0.0',
    DOMPurify: '18.0.0',
    formatDate: '16.0.0',
    getURLParameter: '16.0.0',
    Handlebars: '18.0.0',
    humanFileSize: '16.0.0',
    initCore: '17.0.0',
    jQuery: '19.0.0',
    jstimezonedetect: '18.0.0',
    jstz: '18.0.0',
    md5: '18.0.0',
    moment: '18.0.0',
    oc_appconfig: '17.0.0',
    oc_appswebroots: '17.0.0',
    oc_capabilities: '17.0.0',
    oc_config: '17.0.0',
    oc_current_user: '17.0.0',
    oc_debug: '17.0.0',
    oc_isadmin: '17.0.0',
    oc_requesttoken: '17.0.0',
    oc_webroot: '17.0.0',
    OCDialogs: '17.0.0',
    relative_modified_date: '16.0.0',
};

const oc = {
    _capabilities: '17.0.0',
    addTranslations: '17.0.0',
    basename: '18.0.0',
    coreApps: '17.0.0',
    currentUser: '19.0.0',
    dirname: '18.0.0',
    encodePath: '18.0.0',
    fileIsBlacklisted: '17.0.0',
    filePath: '19.0.0',
    generateUrl: '19.0.0',
    get: '19.0.0',
    getCanonicalLocale: '20.0.0',
    getCurrentUser: '19.0.0',
    getHost: '17.0.0',
    getHostName: '17.0.0',
    getPort: '17.0.0',
    getProtocol: '17.0.0',
    getRootPath: '19.0.0',
    imagePath: '19.0.0',
    isSamePath: '18.0.0',
    joinPaths: '18.0.0',
    linkTo: '19.0.0',
    linkToOCS: '19.0.0',
    linkToRemote: '19.0.0',
    set: '19.0.0',
    webroot: '19.0.0',
};

const oca = {
    Search: '20.0.0',
}

const ocp = {
    Toast: '19.0.0',
}

const oc_sub = {
    Util: {
        formatDate: '20.0.0',
        humanFileSize: '20.0.0',
        relativeModifiedDate: '20.0.0',
    }
};

module.exports = {
    meta: {
        docs: {
            description: "Deprecated Nextcloud APIs",
            category: "Nextcloud",
            recommended: true
        },
        fixable: null,  // or "code" or "whitespace"
        schema: [
            // fill in your schema
        ],
        messages: {
            deprecatedGlobal: "The global property or function {{name}} was deprecated in Nextcloud {{version}}"
        }
    },

    create: function (context) {
        return {
            MemberExpression: function (node) {
                // OC.x
                if (node.object.name === 'OC'
                    && oc.hasOwnProperty(node.property.name)) {
                    context.report(node, "The property or function OC." + node.property.name + " was deprecated in Nextcloud " + oc[node.property.name]);
                }
                // OCA.x
                if (node.object.name === 'OCA'
                    && oca.hasOwnProperty(node.property.name)) {
                    context.report(node, "The property or function OCA." + node.property.name + " was deprecated in Nextcloud " + oca[node.property.name]);
                }
                // OCP.x
                if (node.object.name === 'OCP'
                    && ocp.hasOwnProperty(node.property.name)) {
                    context.report(node, "The property or function OCP." + node.property.name + " was deprecated in Nextcloud " + ocp[node.property.name]);
                }

                // OC.x.y
                if (node.object.type === 'MemberExpression'
                    && node.object.object.name === 'OC'
                    && oc_sub.hasOwnProperty(node.object.property.name)
                    && oc_sub[node.object.property.name].hasOwnProperty(node.property.name)) {
                    const prop = [
                        "OC",
                        node.object.property.name,
                        node.property.name,
                    ].join('.');
                    const version = oc_sub[node.object.property.name][node.property.name]
                    context.report(node, "The property or function " + prop + " was deprecated in Nextcloud " + version);
                }
            },
            Program() {
                // Logic adapted from https://github.com/eslint/eslint/blob/master/lib/rules/no-restricted-globals.js
                const scope = context.getScope();
                const report = ref => {
                    const node = ref.identifier;
                    context.report({
                        node,
                        messageId: 'deprecatedGlobal',
                        data: {
                            name: node.name,
                            version: global[node.name]
                        },
                    });
                }

                // Report variables declared elsewhere (ex: variables defined as "global" by eslint)
                scope.variables.forEach(variable => {
                    if (!variable.defs.length && global.hasOwnProperty(variable.name)) {
                        variable.references.forEach(report);
                    }
                });

                // Report variables not declared at all
                scope.through.forEach(reference => {
                    if (global.hasOwnProperty(reference.identifier.name)) {
                        report(reference);
                    }
                });
            }
        };
    }
};
