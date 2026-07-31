# New Question Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an unlimited, resumable unseen-question mode plus cross-device JSON import/export of learning records.

**Architecture:** Keep the existing zero-dependency single-page structure. Extend `src/app.js` with a unified seen-question store, a validated new-mode session store, and atomic backup merge helpers; reuse the existing exam page renderer for the fourth mode. Extend the Node VM harness so behavior and persistence can be tested without a browser.

**Tech Stack:** Vanilla JavaScript, localStorage, HTML/CSS, Node.js VM tests, Python static build script.

---

### Task 1: Expand the browser test harness

**Files:**
- Create: `tests/test_harness.js`
- Modify: `tests/auto_advance.test.js`

- [ ] **Step 1: Extract a configurable harness**

Create `createApp(options)` supporting `bank`, `storage`, deterministic `Math.random`, captured `alerts`/`confirms`, `FileReader`, `Blob`, `URL.createObjectURL`, anchor clicks, and DOM file input events. Return `{ elements, storage, alerts, confirms, context }`.

- [ ] **Step 2: Switch the existing auto-advance test to the harness**

Replace its embedded fake DOM with:

```javascript
const { createApp, wait } = require("./test_harness");
```

Keep both existing assertions unchanged.

- [ ] **Step 3: Run the regression test**

Run: `node tests\auto_advance.test.js`

Expected: `auto advance tests passed`.

### Task 2: Add unified seen-question tracking

**Files:**
- Create: `tests/seen_tracking.test.js`
- Modify: `src/app.js`

- [ ] **Step 1: Write failing tests**

Cover these exact cases:

```javascript
assert.ok(JSON.parse(storage.get("kemuyi_seen")).q1);
assert.ok(seen.q1, "selected exam answer is seen");
assert.ok(!seen.q2, "unanswered exam question is not seen");
```

Exercise normal practice, wrong practice, and mock grading through UI events.

- [ ] **Step 2: Verify the tests fail**

Run: `node tests\seen_tracking.test.js`

Expected: FAIL because `kemuyi_seen` is not written.

- [ ] **Step 3: Implement the seen store**

Add:

```javascript
var LS_SEEN = "kemuyi_seen";
function loadSeen() { return loadJSON(LS_SEEN, {}); }
function saveSeen(seen) { return saveJSON(LS_SEEN, seen); }
function markSeen(qid, now) {
  var seen = loadSeen();
  if (!seen[qid]) seen[qid] = now || Date.now();
  saveSeen(seen);
}
```

Call `markSeen` from `recordPracticeAnswer`. In `gradeExamAndRecord`, batch-add only indexes where `answers[i] !== undefined`.

- [ ] **Step 4: Run seen and existing tests**

Run:

```powershell
node tests\seen_tracking.test.js
node tests\auto_advance.test.js
```

Expected: both PASS.

### Task 3: Implement the resumable new-question session

**Files:**
- Create: `tests/new_question_mode.test.js`
- Modify: `src/app.js`

- [ ] **Step 1: Write failing mode tests**

Use a bank larger than 100 and assert:

```javascript
assert.strictEqual(Number(elements["total-no"].textContent), bank.length);
assert.strictEqual(elements["timer"].textContent, "无计时");
```

Also test exclusion by `kemuyi_seen`, stable resume order/index/answers/judgments/marks, pruning externally seen unanswered questions, correct auto-next, wrong-answer stay, early-finish preservation, and full-completion clearing.

- [ ] **Step 2: Verify the tests fail**

Run: `node tests\new_question_mode.test.js`

Expected: FAIL because the fourth mode and `kemuyi_new_session` do not exist.

- [ ] **Step 3: Add mode and session helpers**

Add:

```javascript
var MODE = { PRACTICE: "practice", EXAM: "exam", WRONG: "wrong", NEW: "new" };
var LS_NEW_SESSION = "kemuyi_new_session";
```

Implement `validateNewSession`, `loadNewSession`, `saveNewSession`, `clearNewSession`, `buildNewQuestionPaper`, `createNewSession`, and `restoreNewSession`. Session restoration must retain answered session questions and remove externally seen unanswered questions without reordering survivors.

- [ ] **Step 4: Wire the mode into existing state/rendering**

Add a `btn-new` start handler. Reuse practice answer recording, include `MODE.NEW` in the 650ms correct-answer auto-next condition, suppress the timer and display `无计时`, persist after answers/navigation/marks, preserve on manual finish, clear only after natural completion, and make the result action continue the saved session.

- [ ] **Step 5: Run mode tests**

Run:

```powershell
node tests\new_question_mode.test.js
node tests\seen_tracking.test.js
node tests\auto_advance.test.js
```

Expected: all PASS.

### Task 4: Add backup export, validation, and atomic merge import

**Files:**
- Create: `tests/record_transfer.test.js`
- Modify: `src/app.js`

- [ ] **Step 1: Write failing transfer tests**

Test object-valued version-2 backups and string-valued legacy backups. Assert:

```javascript
assert.deepStrictEqual(Object.keys(importedSeen).sort(), ["q1", "q2"]);
assert.strictEqual(mergedWrong.q1.w, 3);
assert.strictEqual(mergedStats.totalAnswered, 12);
```

Also snapshot all five storage keys before malformed import and assert byte-for-byte equality afterward.

- [ ] **Step 2: Verify the tests fail**

Run: `node tests\record_transfer.test.js`

Expected: FAIL because export/import handlers do not exist.

- [ ] **Step 3: Implement backup helpers**

Implement `buildBackup`, `normalizeBackupStorage`, `mergeSm2`, `mergeWrong`, `mergeStats`, `mergeSeen`, and `mergeNewSession`. Parse every incoming value in memory, validate object shapes, infer seen IDs from imported SM-2/wrong records, calculate all merged values, then write all five keys only after validation succeeds.

- [ ] **Step 4: Wire browser export/import**

Bind `btn-export`, `btn-import`, and `import-file`. Export an UTF-8 JSON `Blob`; import with `FileReader`, confirm merge, show success/error alerts, reset the file input, and refresh homepage stats without mutating storage on failure.

- [ ] **Step 5: Run transfer tests**

Run:

```powershell
node tests\record_transfer.test.js
node tests\new_question_mode.test.js
node tests\seen_tracking.test.js
node tests\auto_advance.test.js
```

Expected: all PASS.

### Task 5: Add the fourth mode and data controls to the UI

**Files:**
- Modify: `src/index.template.html`
- Modify: `src/style.css`
- Modify: `README.md`
- Create: `tests/ui_markup.test.js`

- [ ] **Step 1: Write a failing markup test**

Assert the template contains `btn-new`, `new-remaining`, `btn-export`, `btn-import`, and `import-file`, and that README describes four modes and Android Firefox JSON migration.

- [ ] **Step 2: Verify the test fails**

Run: `node tests\ui_markup.test.js`

Expected: FAIL for missing new controls.

- [ ] **Step 3: Add markup and restrained styling**

Add a fourth home mode button with remaining/resume text, a new-mode badge, export/import commands, and a hidden `.json` file input. Keep the existing visual system and use stable responsive dimensions.

- [ ] **Step 4: Update documentation**

Change “three modes” to “four modes”; describe unseen-only selection, unlimited/no-timer resume behavior, export/import merge semantics, and Android Firefox migration.

- [ ] **Step 5: Run markup and behavior tests**

Run:

```powershell
node tests\ui_markup.test.js
node tests\record_transfer.test.js
node tests\new_question_mode.test.js
node tests\seen_tracking.test.js
node tests\auto_advance.test.js
```

Expected: all PASS.

### Task 6: Reset, build, and final verification

**Files:**
- Create: `tests/reset_progress.test.js`
- Modify: `src/app.js`
- Regenerate: `index.html`
- Regenerate: `manifest.json`
- Regenerate: `sw.js`

- [ ] **Step 1: Write a failing reset test**

Seed all five keys, trigger the existing reset command, and assert `kemuyi_seen` plus `kemuyi_new_session` are removed with the legacy keys.

- [ ] **Step 2: Implement reset coverage**

Extend the reset handler to remove `LS_SEEN` and `LS_NEW_SESSION`, cancel pending auto-next, clear active state, and rerender the homepage.

- [ ] **Step 3: Run all tests and syntax check**

Run:

```powershell
node tests\auto_advance.test.js
node tests\seen_tracking.test.js
node tests\new_question_mode.test.js
node tests\record_transfer.test.js
node tests\ui_markup.test.js
node tests\reset_progress.test.js
node --check src\app.js
```

Expected: all tests PASS and syntax check exits 0.

- [ ] **Step 4: Build the distributable page**

Run: `python scripts\build_html.py`

Expected: build completes and regenerates `index.html`, `manifest.json`, `sw.js`, and icons as defined by the script.

- [ ] **Step 5: Inspect generated output**

Run:

```powershell
Select-String -Path index.html -Pattern 'btn-new','kemuyi_seen','kemuyi_new_session','btn-export','btn-import'
```

Expected: every pattern is present.

- [ ] **Step 6: Record the no-Git limitation**

No commit commands are possible because this extracted directory has no `.git` metadata. Preserve all verified files in place and report that limitation with the final test/build results.
