const assert = require("assert");
const { createApp } = require("./test_harness");

function read(storage, key) {
  return JSON.parse(storage.get(key) || "{}");
}

function testPracticeMarksSeen() {
  const { elements, storage } = createApp();
  elements["btn-practice"].onclick();
  elements["q-area"].children[0].onclick();
  assert.ok(read(storage, "kemuyi_seen").q1, "刷题作答应写入已作答记录");
}

function testWrongPracticeMarksSeen() {
  const { elements, storage } = createApp({
    storage: { kemuyi_wrong: { q1: { a: 1, w: 1 } } }
  });
  elements["btn-wrong"].onclick();
  elements["q-area"].children[1].onclick();
  assert.ok(read(storage, "kemuyi_seen").q1, "错题重练作答应写入已作答记录");
}

function testExamOnlyMarksSelectedAnswersSeen() {
  const { elements, storage } = createApp();
  elements["btn-exam"].onclick();
  elements["q-area"].children[0].onclick();
  elements["btn-submit"].onclick();
  const seen = read(storage, "kemuyi_seen");
  assert.ok(seen.q1, "模考中已选择答案的题应计为已作答");
  assert.ok(!seen.q2, "模考中未作答的题不应计为已作答");
}

testPracticeMarksSeen();
testWrongPracticeMarksSeen();
testExamOnlyMarksSelectedAnswersSeen();
console.log("seen tracking tests passed");
