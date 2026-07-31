const assert = require("assert");
const { createApp } = require("./test_harness");

function testShowsLatestThreeByDate() {
  const history = [
    { score: 80, right: 80, wrong: 20, time: 40, date: 1000 },
    { score: 96, right: 96, wrong: 4, time: 35, date: 3000 },
    { score: 92, right: 92, wrong: 8, time: 36, date: 2000 },
    { score: 88, right: 88, wrong: 12, time: 44, date: 4000 }
  ];
  const { context, elements, storage } = createApp({
    storage: { kemuyi_stats: { totalAnswered: 0, totalCorrect: 0, examHistory: history } }
  });

  context.window.__KMY__.renderExamHistory();

  const html = elements["exam-history-list"].innerHTML;
  assert.ok(html.indexOf("88") < html.indexOf("96"), "newest result appears first");
  assert.strictEqual((html.match(/class="exam-history-item/g) || []).length, 3);
  assert.strictEqual(elements["exam-history-toggle"].textContent, "查看全部");
  assert.deepStrictEqual(JSON.parse(storage.get("kemuyi_stats")).examHistory, history);
}

function testExpandsAndCollapsesHistory() {
  const history = [1, 2, 3, 4].map((score, index) => ({
    score: 90 + score,
    right: 90 + score,
    wrong: 10 - score,
    time: 30,
    date: index + 1
  }));
  const { context, elements } = createApp({
    storage: { kemuyi_stats: { examHistory: history } }
  });

  context.window.__KMY__.renderExamHistory();
  elements["exam-history-toggle"].onclick();

  assert.strictEqual((elements["exam-history-list"].innerHTML.match(/class="exam-history-item/g) || []).length, 4);
  assert.strictEqual(elements["exam-history-toggle"].textContent, "收起");

  elements["exam-history-toggle"].onclick();
  assert.strictEqual((elements["exam-history-list"].innerHTML.match(/class="exam-history-item/g) || []).length, 3);
  assert.strictEqual(elements["exam-history-toggle"].textContent, "查看全部");
}

function testEmptyAndMalformedHistoryAreSafe() {
  const { context, elements } = createApp({
    storage: { kemuyi_stats: { examHistory: [{ score: "bad" }, null, "invalid"] } }
  });

  assert.doesNotThrow(() => context.window.__KMY__.renderExamHistory());
  assert.ok(elements["exam-history-list"].innerHTML.includes("还没有模拟考试记录"));
}

testShowsLatestThreeByDate();
testExpandsAndCollapsesHistory();
testEmptyAndMalformedHistoryAreSafe();
console.log("exam history tests passed");
