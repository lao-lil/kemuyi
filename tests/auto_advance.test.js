const assert = require("assert");
const { createApp, wait } = require("./test_harness");

async function testCorrectAnswerAdvances() {
  const { elements } = createApp();
  elements["btn-practice"].onclick();
  assert.strictEqual(elements["cur-no"].textContent, 1);

  elements["q-area"].children[0].onclick();
  await wait(900);

  assert.strictEqual(elements["cur-no"].textContent, 2, "答对刷题应自动进入下一题");

  elements["q-area"].children[0].onclick();
  await wait(900);

  assert.strictEqual(elements["page-result"].classList.contains("hidden"), false, "最后一题答对后应自动进入总结页");
}

async function testWrongAnswerStays() {
  const { elements } = createApp();
  elements["btn-practice"].onclick();
  assert.strictEqual(elements["cur-no"].textContent, 1);

  elements["q-area"].children[1].onclick();
  await wait(900);

  assert.strictEqual(elements["cur-no"].textContent, 1, "答错后应停留以查看解析");
  elements["btn-submit"].onclick();
}

(async function () {
  await testCorrectAnswerAdvances();
  await testWrongAnswerStays();
  console.log("auto advance tests passed");
  process.exit(0);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});


