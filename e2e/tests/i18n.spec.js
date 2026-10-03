const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { test, expect } = require("@playwright/test");

// 前端没有跑单测的框架，而 i18n.js 只是导出一个普通对象字面量 ——
// 把 import / export 两行剥掉、给 createI18n 一个空壳，就能在 vm 里求值拿到 messages。
// 这样检查的是真实源文件，不用把翻译表复制一份到测试里。
const I18N_PATH = path.resolve(__dirname, "..", "..", "frontend", "src", "i18n.js");

function loadMessages() {
  const source = fs
    .readFileSync(I18N_PATH, "utf8")
    .replace(/^import\s[^\n]*\n/m, "")
    .replace(/^export\s+default\s[^\n]*\n/m, "");

  const context = { createI18n: () => ({}) };
  vm.createContext(context);
  vm.runInContext(`${source}\nglobalThis.__messages = messages;`, context);
  return context.__messages;
}

function collectLeafKeys(node, prefix = "") {
  const keys = [];
  for (const [key, value] of Object.entries(node)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === "object") {
      keys.push(...collectLeafKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

function placeholders(text) {
  return [...String(text).matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
}

test.describe("中英文案一致性", () => {
  const messages = loadMessages();

  test("两种语言都定义了，且根节点结构相同", () => {
    expect(Object.keys(messages).sort()).toEqual(["cn", "en"]);
    expect(Object.keys(messages.cn).sort()).toEqual(Object.keys(messages.en).sort());
  });

  test("每个 key 中英都有，没有单边漏翻", () => {
    const cn = new Set(collectLeafKeys(messages.cn));
    const en = new Set(collectLeafKeys(messages.en));

    // 只 cn 有 = 英文漏翻；只 en 有 = 中文漏翻
    const missingInEn = [...cn].filter((key) => !en.has(key)).sort();
    const missingInCn = [...en].filter((key) => !cn.has(key)).sort();

    expect(
      { missingInEn, missingInCn },
      `中英 key 对不上：\n  缺少英文：${missingInEn.join(", ") || "无"}\n  缺少中文：${missingInCn.join(", ") || "无"}`
    ).toEqual({ missingInEn: [], missingInCn: [] });
  });

  test("同一条文案的插值占位符中英一致", () => {
    const mismatched = [];
    for (const key of collectLeafKeys(messages.cn)) {
      const cnValue = key.split(".").reduce((node, part) => node?.[part], messages.cn);
      const enValue = key.split(".").reduce((node, part) => node?.[part], messages.en);
      if (typeof cnValue !== "string" || typeof enValue !== "string") continue;

      const [cnSlots, enSlots] = [placeholders(cnValue), placeholders(enValue)];
      if (cnSlots.join() !== enSlots.join()) {
        mismatched.push(`${key}: cn={${cnSlots.join()}} en={${enSlots.join()}}`);
      }
    }

    expect(mismatched, `占位符对不上：\n  ${mismatched.join("\n  ")}`).toEqual([]);
  });
});
