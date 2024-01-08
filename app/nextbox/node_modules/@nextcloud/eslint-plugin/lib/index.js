/**
 * @fileoverview Nextcloud lint plugin for ESLint
 * @author Christoph Wurst
 */
"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

var requireIndex = require("requireindex");

//------------------------------------------------------------------------------
// Plugin Definition
//------------------------------------------------------------------------------


// import all rules in lib/rules
module.exports.rules = requireIndex(__dirname + "/rules");

// import all environments in lib/environments
module.exports.environments = requireIndex(__dirname + "/environments");

// import all configs in lib/configs
module.exports.configs = requireIndex(__dirname + "/configs");
