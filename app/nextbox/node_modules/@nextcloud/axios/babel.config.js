module.exports = {
    presets: [
        "@babel/typescript",
        [
            "@babel/env",
            {
                useBuiltIns: "usage",
                corejs: "3.0.0",
            },
        ],
    ]
};
