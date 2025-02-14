module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    "plugin:vue/vue3-essential",
    "eslint:recommended",
    "plugin:prettier/recommended",
  ],
  parser: "@babel/eslint-parser", // 使用 Babel 的解析器
  parserOptions: {
    requireConfigFile: false, // 不强制要求 Babel 配置文件
    babelOptions: {
      presets: ["@babel/preset-env"], // 告诉 ESLint 使用 Babel 配置
    },
  },
  rules: {
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    "prettier/prettier": "off",
  },
};
