# Recent Exam Scores Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an inline homepage summary of the latest three mock-exam results with a control to expand the full stored history.

**Architecture:** Reuse the existing `kemuyi_stats.examHistory` localStorage data and single-page DOM. Add one focused renderer in `src/app.js`, markup in the existing cover-page template, and CSS that follows the current compact mobile-first visual system. Keep the feature read-only so mock-exam grading and persistence remain unchanged.

**Tech Stack:** Vanilla JavaScript, HTML/CSS, localStorage, Node.js VM test harness, Python build script.

---

### Task 1: Add failing behavior tests for history rendering

**Files:**
- Create: `tests/exam_history.test.js`
- Read: `tests/test_harness.js`
- Read: `src/app.js`

- [ ] **Step 1: Write the failing test**

Create a test that initializes the real app code through `createApp`, seeds `kemuyi_stats.examHistory`, and verifies the homepage renderer's observable DOM output:

```javascript
const assert = require("assert");
const { createApp } = require("./test_harness");

function readHistory(storage) {
  return JSON.parse(storage.get("kemuyi_stats")).examHistory;
}

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
  assert.deepStrictEqual(readHistory(storage), history);
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
node tests\exam_history.test.js
```

Expected: FAIL because the new DOM elements and `renderExamHistory` export do not exist.

### Task 2: Implement the history renderer and template controls

**Files:**
- Modify: `src/index.template.html`
- Modify: `src/app.js`

- [ ] **Step 1: Add the homepage markup**

Insert below the existing `.stats-row` in `src/index.template.html`:

```html
  <section class="exam-history-panel" aria-labelledby="exam-history-title">
    <div class="exam-history-heading">
      <h3 id="exam-history-title">最近模拟考试</h3>
      <button class="history-toggle hidden" id="exam-history-toggle" type="button">查看全部</button>
    </div>
    <div id="exam-history-list"></div>
  </section>
```

- [ ] **Step 2: Add the failing-test implementation**

In `src/app.js`, add page-local state near the other top-level state variables:

```javascript
var examHistoryExpanded = false;
```

Add these helpers near the existing stats rendering functions:

```javascript
function formatExamHistoryDate(value) {
  var date = new Date(Number(value));
  if (!Number.isFinite(date.getTime())) return "时间未知";
  return date.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function normalizeExamHistoryItem(item) {
  if (!item || typeof item !== "object") return null;
  var score = Number(item.score);
  var time = Number(item.time);
  var date = Number(item.date);
  if (!Number.isFinite(score) || !Number.isFinite(date)) return null;
  return {
    score: Math.max(0, Math.round(score)),
    right: Number.isFinite(Number(item.right)) ? Math.max(0, Math.round(Number(item.right))) : null,
    wrong: Number.isFinite(Number(item.wrong)) ? Math.max(0, Math.round(Number(item.wrong))) : null,
    time: Number.isFinite(time) ? Math.max(0, Math.round(time)) : null,
    date: date,
    timeout: item.timeout === true
  };
}

function renderExamHistory(expanded) {
  if (expanded !== undefined) examHistoryExpanded = !!expanded;
  var list = $("exam-history-list");
  var toggle = $("exam-history-toggle");
  if (!list || !toggle) return;

  var stats = loadStats();
  var history = Array.isArray(stats.examHistory) ? stats.examHistory
    .map(normalizeExamHistoryItem)
    .filter(Boolean)
    .sort(function (a, b) { return b.date - a.date; }) : [];

  if (history.length === 0) {
    list.innerHTML = '<div class="exam-history-empty">还没有模拟考试记录</div>';
    toggle.classList.add("hidden");
    return;
  }

  var visible = examHistoryExpanded ? history : history.slice(0, 3);
  list.innerHTML = visible.map(function (item) {
    var pass = item.score >= 90;
    var detail = item.time === null ? "用时 —" : "用时 " + item.time + " 分钟";
    if (item.timeout) detail += " · 超时";
    return '<div class="exam-history-item">' +
      '<div><span class="exam-history-date">' + escapeHtml(formatExamHistoryDate(item.date)) + '</span>' +
      '<span class="exam-history-detail">' + escapeHtml(detail) + '</span></div>' +
      '<div class="exam-history-score ' + (pass ? "pass" : "fail") + '">' +
      '<b>' + item.score + '</b> 分 · ' + (pass ? "合格" : "未合格") + '</div>' +
      '</div>';
  }).join("");

  toggle.classList.toggle("hidden", history.length <= 3);
  toggle.textContent = examHistoryExpanded ? "收起" : "查看全部";
}
```

Use the app's existing HTML escaping helper if present; otherwise add a small `escapeHtml` helper beside the renderer that replaces `&`, `<`, `>`, `"`, and `'`. Bind the toggle in the existing startup binding section:

```javascript
$("exam-history-toggle").onclick = function () {
  renderExamHistory(!examHistoryExpanded);
};
```

Call `renderExamHistory(false)` from the existing homepage refresh function so it runs on initial load and whenever the result page returns home. Export `renderExamHistory` through `window.__KMY__` for the VM test harness.

- [ ] **Step 3: Run the behavior test to verify it passes**

Run:

```powershell
node tests\exam_history.test.js
```

Expected: `exam history tests passed`.

### Task 3: Add styles and markup regression coverage

**Files:**
- Modify: `src/style.css`
- Modify: `tests/ui_markup.test.js`

- [ ] **Step 1: Extend the markup test**

Add these IDs to the existing required-ID list in `tests/ui_markup.test.js`:

```javascript
"exam-history-title", "exam-history-list", "exam-history-toggle"
```

Also assert:

```javascript
assert.ok(html.includes("最近模拟考试"));
```

- [ ] **Step 2: Add focused CSS**

Append styles using the existing variables in `src/style.css`:

```css
.exam-history-panel {
  margin-top: 16px;
  text-align: left;
}
.exam-history-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.exam-history-heading h3 {
  margin: 0;
  font-size: 15px;
}
.history-toggle {
  border: 0;
  background: transparent;
  color: var(--blue);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 0;
}
.exam-history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 46px;
  padding: 9px 0;
  border-bottom: 1px solid var(--line);
}
.exam-history-date {
  display: block;
  color: var(--gray-8);
  font-size: 13px;
}
.exam-history-detail {
  display: block;
  margin-top: 3px;
  color: var(--gray-6);
  font-size: 11px;
}
.exam-history-score {
  flex: 0 0 auto;
  font-size: 12px;
  white-space: nowrap;
}
.exam-history-score b {
  font-size: 18px;
}
.exam-history-score.pass { color: var(--green); }
.exam-history-score.fail { color: var(--orange); }
.exam-history-empty {
  padding: 14px 0;
  color: var(--gray-6);
  font-size: 12px;
  text-align: center;
}
```

- [ ] **Step 3: Run markup and behavior tests**

Run:

```powershell
node tests\ui_markup.test.js
node tests\exam_history.test.js
```

Expected: both tests pass.

### Task 4: Verify integration, build the distributable page, and update documentation

**Files:**
- Modify: `README.md`
- Regenerate: `index.html`
- Regenerate: `manifest.json`
- Regenerate: `sw.js`

- [ ] **Step 1: Update README feature description**

Add to the “学习数据持久化” section:

```markdown
- 首页会显示最近 3 次模拟考试成绩，可展开查看最多 50 次模考历史。
```

- [ ] **Step 2: Run all existing and new tests**

Run:

```powershell
node tests\auto_advance.test.js
node tests\seen_tracking.test.js
node tests\new_question_mode.test.js
node tests\record_transfer.test.js
node tests\ui_markup.test.js
node tests\reset_progress.test.js
node tests\exam_history.test.js
node --check src\app.js
```

Expected: every test prints its `... tests passed` message and syntax checking exits with code 0.

- [ ] **Step 3: Build the single-file PWA**

Run:

```powershell
python scripts\build_html.py
```

Expected: the script regenerates `index.html`, `manifest.json`, and `sw.js` without errors.

- [ ] **Step 4: Inspect generated output**

Run:

```powershell
Select-String -Path index.html -Pattern 'exam-history-title','exam-history-list','exam-history-toggle','renderExamHistory'
```

Expected: every pattern is present in the generated HTML.

- [ ] **Step 5: Manually smoke-test the built page**

Open the generated `index.html` in a browser with existing `kemuyi_stats.examHistory` data, confirm:

1. No history shows the empty state.
2. Four records show only three rows and a “查看全部” control.
3. Clicking “查看全部” shows all four, and “收起” returns to three.
4. A score of 90 is labeled “合格”.
5. Starting and finishing a new mock exam still adds a record and refreshes the homepage list.
