"use strict";

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

const global = {
    escapeHTML: '20.0.0',
    fileDownloadPath: '15.0.0',
    formatDate: '19.0.0',
    getScrollBarWidth: '15.0.0',
    getURLParameter: '19.0.0',
    humanFileSize: '19.0.0',
    marked: '19.0.0',
    relative_modified_date: '19.0.0',
}

const oc = {
    getScrollBarWidth: '15.0.0',
}

const oc_sub = {
    AppConfig: {
        hasKey: '15.0.0',
        deleteApp: '15.0.0',
    },
    Util: {
        hasSVGSupport: '15.0.0',
        replaceSVGIcon: '15.0.0',
        replaceSVG: '15.0.0',
        scaleFixForIE8: '15.0.0',
        isIE8: '15.0.0',
    },
}

// TODO: handle OC.x.y.z like OC.Share.ShareConfigModel.areAvatarsEnabled()
//       ref https://github.com/nextcloud/server/issues/11045

module.exports = {
    meta: {
        docs: {
            description: "Removed Nextcloud APIs",
            category: "Nextcloud",
            recommended: true
        },
        fixable: null,  // or "code" or "whitespace"
        schema: [
            // fill in your schema
        ],
        messages: {
            removedGlobal: "The global property or function {{name}} was removed in Nextcloud {{version}}"
        }
    },

    create: function (context) {
        return {
            MemberExpression: function (node) {
                // OC.x
                if (node.object.name === 'OC'
                    && oc.hasOwnProperty(node.property.name)) {
                    context.report(node, "The property or function OC." + node.property.name + " was removed in Nextcloud " + oc[node.property.name]);
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
                    context.report(node, "The property or function " + prop + " was removed in Nextcloud " + version);
                }
            },
            Program() {
                // Logic adapted from https://github.com/eslint/eslint/blob/master/lib/rules/no-restricted-globals.js
                const scope = context.getScope();
                const report = ref => {
                    const node = ref.identifier;
                    context.report({
                        node,
                        messageId: 'removedGlobal',
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
