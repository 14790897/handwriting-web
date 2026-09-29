const assert = require("assert").strict;

const tests = [];
function test(name, run) {
  tests.push({ name, run });
}

const formatterModule = import("../src/utils/chineseLetterFormatter.mjs");

test("extracts a trailing signature and Chinese date", async () => {
  const { extractLetterEnding } = await formatterModule;
  const result = extractLetterEnding(
    "第一段。\r\n\r\n第二段。\n\n张三\n2026年7月26日"
  );

  assert.equal(result.body, "第一段。\n\n第二段。");
  assert.equal(result.signature, "张三");
  assert.equal(result.date, "2026年7月26日");
  assert.equal(result.detectedEnding, true);
});

test("indents paragraphs, removes empty lines, and right-aligns the ending", async () => {
  const { formatChineseLetter } = await formatterModule;
  const result = formatChineseLetter({
    body: "第一段。\n\n　　第二段。",
    signature: "张三",
    date: "2026年7月26日",
  });

  assert.equal(
    result,
    "　　第一段。\n　　第二段。\n>>>张三\n>>>2026年7月26日"
  );
});

test("preserves manual page breaks and existing right-aligned lines", async () => {
  const { formatChineseLetter } = await formatterModule;
  const result = formatChineseLetter({
    body: "第一页\n\n---\n第二页\n>>>已有落款",
  });

  assert.equal(result, "　　第一页\n---\n　　第二页\n>>>已有落款");
});

test("does not treat a sentence before the date as a signature", async () => {
  const { extractLetterEnding } = await formatterModule;
  const result = extractLetterEnding("这是正文。\n2026-07-26");

  assert.equal(result.body, "这是正文。");
  assert.equal(result.signature, "");
  assert.equal(result.date, "2026-07-26");
});

test("keeps a leading salutation flush left", async () => {
  const { formatChineseLetter } = await formatterModule;
  const result = formatChineseLetter({
    body: "亲爱的妈妈：\n最近一切都好。",
    signature: "小明",
    date: "2026年7月26日",
  });

  assert.equal(
    result,
    "亲爱的妈妈：\n　　最近一切都好。\n>>>小明\n>>>2026年7月26日"
  );
});

test("formatting an already formatted letter is idempotent", async () => {
  const { extractLetterEnding, formatChineseLetter } = await formatterModule;
  const original =
    "亲爱的妈妈：\n　　第一段。\n　　第二段。\n>>>小明\n>>>2026年7月26日";
  const ending = extractLetterEnding(original);
  const result = formatChineseLetter({
    body: ending.body,
    signature: ending.signature,
    date: ending.date,
  });

  assert.equal(result, original);
});

test("extracts and right-aligns a two-line signature block", async () => {
  const { extractLetterEnding, formatChineseLetter } = await formatterModule;
  const ending = extractLetterEnding(
    "妈：\n正文最后一句。\n爱你的儿子\n佳佳\n2026 年 7 月 26 日"
  );

  assert.equal(ending.body, "妈：\n正文最后一句。");
  assert.equal(ending.signature, "爱你的儿子\n佳佳");
  assert.equal(
    formatChineseLetter(ending),
    "妈：\n　　正文最后一句。\n>>>爱你的儿子\n>>>佳佳\n>>>2026 年 7 月 26 日"
  );
});

test("does not absorb a short closing sentence into the signature", async () => {
  const { extractLetterEnding } = await formatterModule;
  const ending = extractLetterEnding("正文。\n保重\n张三\n2026年7月26日");

  assert.equal(ending.body, "正文。\n保重");
  assert.equal(ending.signature, "张三");
});

test("keeps a blessing in the body when no signature is present", async () => {
  const { extractLetterEnding } = await formatterModule;
  const ending = extractLetterEnding("正文。\n祝身体健康\n2026年7月27日");

  assert.equal(ending.body, "正文。\n祝身体健康");
  assert.equal(ending.signature, "");
  assert.equal(ending.date, "2026年7月27日");
});

test("recognizes a short month-and-day date", async () => {
  const { extractLetterEnding } = await formatterModule;
  const ending = extractLetterEnding("正文。\n张三\n7月27日");

  assert.equal(ending.body, "正文。");
  assert.equal(ending.signature, "张三");
  assert.equal(ending.date, "7月27日");
});

test("formats a body-only letter without adding an ending", async () => {
  const { formatChineseLetter } = await formatterModule;

  assert.equal(
    formatChineseLetter({ body: "妈妈：\n\n最近一切都好。" }),
    "妈妈：\n　　最近一切都好。"
  );
});

test("recognizes a signature without a date", async () => {
  const { extractLetterEnding } = await formatterModule;
  const ending = extractLetterEnding("正文。\n张三");

  assert.equal(ending.body, "正文。");
  assert.equal(ending.signature, "张三");
  assert.equal(ending.date, "");
});

test("restores a falsely detected ending to the body", async () => {
  const { extractLetterEnding, restoreLetterEnding } = await formatterModule;
  const original = "正文。\n早点睡\n2026年7月27日";
  const ending = extractLetterEnding(original);

  assert.equal(restoreLetterEnding(ending), original);
});

(async () => {
  for (const { name, run } of tests) {
    await run();
    console.log(`✓ ${name}`);
  }
  console.log(`${tests.length} tests passed`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
