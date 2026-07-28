const FULL_WIDTH_INDENT = "\u3000\u3000";
const RIGHT_ALIGN_RE = /^[ \t]*>>>[ \t]?/;
const PAGE_BREAK_RE = /^-{3,}$/;
const ARABIC_DATE_RE = /^\d{4}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?$/;
const SHORT_DATE_RE = /^(?:\d{1,2}\s*月\s*\d{1,2}\s*日|\d{1,2}[./-]\d{1,2})$/;
const CHINESE_DATE_RE =
  /^(?:[〇零一二三四五六七八九]{4}年)?[〇零一二三四五六七八九十廿卅]+月[〇零一二三四五六七八九十廿卅]+日$/;

function normalizeNewlines(text) {
  return String(text || "").replace(/\r\n?/g, "\n");
}

function stripRightAlignMarker(line) {
  return String(line || "").replace(RIGHT_ALIGN_RE, "").trim();
}

function looksLikeDate(line) {
  const value = stripRightAlignMarker(line);
  return (
    ARABIC_DATE_RE.test(value) ||
    SHORT_DATE_RE.test(value) ||
    CHINESE_DATE_RE.test(value)
  );
}

function looksLikeSignature(line) {
  const value = stripRightAlignMarker(line);
  if (!value || value.length > 24 || PAGE_BREAK_RE.test(value)) return false;
  if (/[。！？!?；;，,：:]$/.test(value)) return false;
  if (/^(?:祝|愿|请|望|盼|保重|谢谢|感谢|再见|晚安|早安|一切|身体|工作|生活|正文|此致|敬礼|我|我们|你|您)/.test(value)) {
    return false;
  }
  return (
    looksLikeSignaturePrefix(value) ||
    /^[\u3400-\u9fff·]{2,4}$/.test(value) ||
    /^[A-Za-z][A-Za-z .'-]{1,30}$/.test(value) ||
    /(?:敬上|谨上|谨启)$/.test(value)
  );
}

function looksLikeSignaturePrefix(line) {
  const value = stripRightAlignMarker(line);
  return (
    /^(?:爱你的|想你的|牵挂你的).{0,12}$/.test(value) ||
    /^(?:你的)?(?:儿子|女儿|父亲|母亲|爸爸|妈妈|朋友|同学|学生|晚辈|老师|爱人|丈夫|妻子)[：:]?.*$/.test(
      value
    ) ||
    /^(?:敬上|谨上|谨启)$/.test(value)
  );
}

function looksLikeSalutation(line) {
  const value = stripRightAlignMarker(line);
  return value.length <= 30 && /[：:]$/.test(value);
}

export function extractLetterEnding(text) {
  const lines = normalizeNewlines(text).split("\n");
  const contentIndexes = lines
    .map((line, index) => (line.trim() ? index : -1))
    .filter((index) => index >= 0);

  if (contentIndexes.length === 0) {
    return { body: "", signature: "", date: "", detectedEnding: false };
  }

  const removedIndexes = new Set();
  const lastIndex = contentIndexes[contentIndexes.length - 1];
  const previousIndex = contentIndexes[contentIndexes.length - 2];
  const lastLine = lines[lastIndex];
  const previousLine = previousIndex === undefined ? "" : lines[previousIndex];
  const lastIsRightAligned = RIGHT_ALIGN_RE.test(lastLine);
  const previousIsRightAligned = RIGHT_ALIGN_RE.test(previousLine);

  let signature = "";
  let date = "";

  if (looksLikeDate(lastLine) || (lastIsRightAligned && previousIsRightAligned)) {
    date = stripRightAlignMarker(lastLine);
    removedIndexes.add(lastIndex);

    const signatureLines = [];
    for (let offset = contentIndexes.length - 2; offset >= 0; offset -= 1) {
      if (signatureLines.length >= 2) break;
      const candidateIndex = contentIndexes[offset];
      const candidateLine = lines[candidateIndex];
      const isRightAligned = RIGHT_ALIGN_RE.test(candidateLine);
      const isNearestToDate = signatureLines.length === 0;
      const isSignatureLine = isNearestToDate
        ? looksLikeSignature(candidateLine)
        : looksLikeSignaturePrefix(candidateLine);
      if (!isRightAligned && !isSignatureLine) {
        break;
      }
      signatureLines.unshift(stripRightAlignMarker(candidateLine));
      removedIndexes.add(candidateIndex);
    }
    signature = signatureLines.join("\n");
  } else if (lastIsRightAligned || looksLikeSignature(lastLine)) {
    signature = stripRightAlignMarker(lastLine);
    removedIndexes.add(lastIndex);
  }

  const body = lines
    .filter((_, index) => !removedIndexes.has(index))
    .join("\n")
    .trim();

  return {
    body,
    signature,
    date,
    detectedEnding: removedIndexes.size > 0,
  };
}

export function restoreLetterEnding({ body, signature = "", date = "" }) {
  return [body, signature, date]
    .map((value) => normalizeNewlines(value).trim())
    .filter(Boolean)
    .join("\n");
}

export function formatChineseLetter({ body, signature = "", date = "" }) {
  const bodyLines = normalizeNewlines(body)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      if (PAGE_BREAK_RE.test(line)) return line;
      if (RIGHT_ALIGN_RE.test(line)) return `>>>${stripRightAlignMarker(line)}`;
      if (index === 0 && looksLikeSalutation(line)) return line;
      return `${FULL_WIDTH_INDENT}${line.replace(/^[\s\u3000]+/, "")}`;
    });

  const endingLines = [
    ...normalizeNewlines(signature).split("\n"),
    ...normalizeNewlines(date).split("\n"),
  ]
    .map(stripRightAlignMarker)
    .filter(Boolean)
    .map((line) => `>>>${line}`);

  return [...bodyLines, ...endingLines].join("\n");
}
