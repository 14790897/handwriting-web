// 生产站单次最多生成的页数。
//
// 这个上限在 25bad47（"feat: 主站最多一次十页"）里定为 10，界面提示、弹窗和截断都用它。
// 后来 ee944c8c（"fix: rm zip"）把它改成了 15，只有截断跟着变、文案没动，于是用户被告知
// 「最多 10 页」却拿到 15 页（issue #72）。抽成一个常量，让三处共用一个来源。
export const MAX_PAGES = 10;

// 预计页数是否超过上限；只有超过时才需要弹窗确认。
export function exceedsPageLimit(estimatedPages) {
  return estimatedPages > MAX_PAGES;
}

// 页数限制弹窗的文案。提到页数的地方一律从 MAX_PAGES 取，
// 免得哪天再改上限时又只改了截断、忘了文案。
export function buildPageLimitDialog(estimatedPages) {
  return {
    title: "页数限制提醒",
    html: `
            <div style="text-align: left; line-height: 1.6;">
              <p><strong>检测到您的文本预计会生成 ${estimatedPages} 页</strong></p>
              <p>由于服务器资源限制，在 <strong>handwrite.14790897.xyz</strong> 网站上单次最多只能生成 <strong>${MAX_PAGES}页</strong>。</p>
              <p>如果您选择继续：</p>
              <ul style="margin: 10px 0; padding-left: 20px;">
                <li>系统将只生成前 ${MAX_PAGES} 页内容</li>
                <li>超出部分将被自动截断</li>
                <li>建议您分批处理长文本</li>
              </ul>
              <p style="color: #666; font-size: 14px;">
                💡 提示：您可以将长文本分成多个部分，分别生成，或者自行搭建本项目来处理更长的文本
              </p>
              <p style="color: #888; font-size: 12px; margin-top: 10px;">
                注：此限制仅适用于 handwrite.14790897.xyz 网站
              </p>
            </div>
          `,
    confirmText: `继续生成（前${MAX_PAGES}页）`,
    fallbackConfirmText: `检测到您的文本预计会生成 ${estimatedPages} 页。\n\n由于服务器资源限制，在 handwrite.14790897.xyz 网站上单次最多只能生成 ${MAX_PAGES}页。\n\n是否继续生成前${MAX_PAGES}页？`,
  };
}
