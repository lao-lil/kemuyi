const assert = require("assert");
const { createApp, wait } = require("./test_harness");

function makeBank(size) {
  return Array.from({ length: size }, (_, i) => ({
    id: "q" + (i + 1),
    type: "single",
    category: "law",
    question: "题目" + (i + 1),
    options: ["正确", "错误"],
    answer: 0
  }));
}

function read(storage, key) {
  const value = storage.get(key);
  return value == null ? null : JSON.parse(value);
}

function testUnlimitedUnseenPaper() {
  const bank = makeBank(105);
  const { elements, storage } = createApp({
    bank,
    storage: { kemuyi_seen: { q1: 1, q2: 2 } }
  });
  elements["btn-new"].onclick();
  assert.strictEqual(Number(elements["cur-total"].textContent), 103, "新题模式不应限制为100题");
  assert.strictEqual(elements["timer"].textContent, "无计时");
  assert.strictEqual(read(storage, "kemuyi_new_session").questionIds.length, 103);
}

async function testAnswerBehaviorAndCompletion() {
  const { elements, storage } = createApp({ bank: makeBank(2) });
  elements["btn-new"].onclick();
  elements["q-area"].children[1].onclick();
  await wait(800);
  assert.strictEqual(Number(elements["cur-no"].textContent), 1, "新题答错应停留");
  elements["btn-next"].onclick();
  elements["q-area"].children[0].onclick();
  await wait(800);
  assert.strictEqual(elements["page-result"].classList.contains("hidden"), false);
  assert.strictEqual(storage.has("kemuyi_new_session"), false, "自然完成全部新题应清除会话");
}

function testResumeAndPrune() {
  const session = {
    version: 1,
    questionIds: ["q1", "q2", "q3"],
    idx: 1,
    answers: { "0": 1 },
    judged: { "0": false },
    marks: { "0": 1 },
    startedAt: 10,
    updatedAt: 20
  };
  const { elements, storage } = createApp({
    bank: makeBank(3),
    storage: {
      kemuyi_seen: { q1: 5, q2: 6 },
      kemuyi_new_session: session
    }
  });
  elements["btn-new"].onclick();
  const restored = read(storage, "kemuyi_new_session");
  assert.deepStrictEqual(Array.from(restored.questionIds), ["q1", "q3"], "应保留会话内已答题并剔除外部已答的未答题");
  assert.strictEqual(restored.idx, 1);
  assert.strictEqual(Number(elements["cur-no"].textContent), 2);
}

function testEarlyFinishPreservesSession() {
  const { elements, storage } = createApp({ bank: makeBank(3) });
  elements["btn-new"].onclick();
  elements["q-area"].children[0].onclick();
  elements["btn-submit"].onclick();
  assert.ok(storage.has("kemuyi_new_session"), "主动提前结束应保留新题会话");
  assert.strictEqual(elements["btn-again"].textContent, "继续新题");
}

(async function () {
  testUnlimitedUnseenPaper();
  await testAnswerBehaviorAndCompletion();
  testResumeAndPrune();
  testEarlyFinishPreservesSession();
  console.log("new question mode tests passed");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
