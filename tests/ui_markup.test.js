const assert = require("assert");
const fs = require("fs");

const html = fs.readFileSync(require.resolve("../src/index.template.html"), "utf8");
const readme = fs.readFileSync(require.resolve("../README.md"), "utf8");

["btn-new", "new-remaining", "btn-export", "btn-import", "import-file", "mb-new",
  "exam-history-title", "exam-history-list", "exam-history-toggle"].forEach((id) => {
  assert.ok(html.includes(`id="${id}"`), `模板缺少 ${id}`);
});
assert.ok(html.includes("四种模式说明"));
assert.ok(html.includes("最近模拟考试"));
assert.ok(readme.includes("新题连续练习"));
assert.ok(readme.includes("Android Firefox"));
console.log("ui markup tests passed");
