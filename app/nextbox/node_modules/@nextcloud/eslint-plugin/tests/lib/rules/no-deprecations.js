/**
 * @fileoverview tbd
 * @author Christoph Wurst
 */
"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

var rule = require("../../../lib/rules/no-deprecations"),

    RuleTester = require("eslint").RuleTester;


//------------------------------------------------------------------------------
// Tests
//------------------------------------------------------------------------------

var ruleTester = new RuleTester();
ruleTester.run("no-deprecations", rule, {

    valid: [
        {
            code: "var escapeHTML = require('escape-html'); var sanitized = escapeHTML('hello')",
        }
    ],

    invalid: [
        {
            code: "var date = relative_modified_date(123)",
            errors: [{
                message: "The global property or function relative_modified_date was deprecated in Nextcloud 16.0.0",
                type: "Identifier"
            }]
        },
        {
            code: "$('body').text()",
            errors: [{
                message: "The global property or function $ was deprecated in Nextcloud 19.0.0",
                type: "Identifier"
            }]
        },
        {
            code: "OC.getHost()",
            errors: [{
                message: "The property or function OC.getHost was deprecated in Nextcloud 17.0.0",
                type: "MemberExpression"
            }]
        },
        {
            code: "OCP.Toast.success('hello')",
            errors: [{
                message: "The property or function OCP.Toast was deprecated in Nextcloud 19.0.0",
                type: "MemberExpression"
            }]
        },
        {
            code: "var clean = DOMPurify.sanitize(dirty);",
            errors: [{
                message: "The global property or function DOMPurify was deprecated in Nextcloud 18.0.0",
                type: "Identifier"
            }]
        }
    ]
});
