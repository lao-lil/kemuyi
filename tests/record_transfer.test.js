const assert = require("assert");
const { createApp } = require("./test_harness");

function read(storage, key) {
  const value = storage.get(key);
  return value == null ? null : JSON.parse(value);
}

function testLegacyImportAndSeenInference() {
  const { context, storage } = createApp();
  const legacy = {
    kemuyi_sm2: JSON.stringify({ q1: { ease: 2.5, interval: 1, reps: 1, due: 2, last: 10 } }),
    kemuyi_wrong: JSON.stringify({ q2: { a: 20, w: 2 } }),
    kemuyi_stats: JSON.stringify({ totalAnswered: 7, totalCorrect: 5, examHistory: [], studyDays: {} })
  };
  context.window.__KMY__.importBackupObject(legacy);
  assert.deepStrictEqual(Object.keys(read(storage, "kemuyi_seen")).sort(), ["q1", "q2"]);
  assert.strictEqual(read(storage, "kemuyi_stats").totalAnswered, 7);
}

function testRemoteDebugDataWrapperImport() {
  const { context, storage } = createApp();
  context.window.__KMY__.importBackupObject({
    version: 1,
    exportedAt: "2026-07-30T13:17:16.847Z",
    data: {
      kemuyi_sm2: JSON.stringify({ q1: { ease: 2.5, interval: 3, reps: 2, due: 4, last: 30 } }),
      kemuyi_wrong: JSON.stringify({ q2: { a: 40, w: 1 } }),
      kemuyi_stats: JSON.stringify({ totalAnswered: 9, totalCorrect: 6, examHistory: [], studyDays: {} })
    }
  });
  assert.strictEqual(read(storage, "kemuyi_stats").totalAnswered, 9);
  assert.deepStrictEqual(Object.keys(read(storage, "kemuyi_seen")).sort(), ["q1", "q2"]);
}

function testVersionTwoMerge() {
  const { context, storage } = createApp({
    storage: {
      kemuyi_wrong: { q1: { a: 10, w: 1 } },
      kemuyi_stats: { totalAnswered: 12, totalCorrect: 9, examHistory: [], studyDays: { "2026-07-30": 1 } },
      kemuyi_seen: { q1: 30 }
    }
  });
  context.window.__KMY__.importBackupObject({
    app: "driving-test-subject1",
    version: 2,
    storage: {
      kemuyi_sm2: {},
      kemuyi_wrong: { q1: { a: 20, w: 3 } },
      kemuyi_stats: { totalAnswered: 8, totalCorrect: 7, examHistory: [], studyDays: { "2026-07-29": 1 } },
      kemuyi_seen: { q2: 40 },
      kemuyi_new_session: null
    }
  });
  assert.strictEqual(read(storage, "kemuyi_wrong").q1.w, 3);
  assert.strictEqual(read(storage, "kemuyi_wrong").q1.a, 20);
  assert.strictEqual(read(storage, "kemuyi_stats").totalAnswered, 12);
  assert.deepStrictEqual(Object.keys(read(storage, "kemuyi_seen")).sort(), ["q1", "q2"]);
}

function testInvalidImportIsAtomic() {
  const seed = {
    kemuyi_sm2: { q1: { ease: 2.5, interval: 1, reps: 1, due: 2, last: 1 } },
    kemuyi_wrong: {},
    kemuyi_stats: { totalAnswered: 1, totalCorrect: 1, examHistory: [], studyDays: {} },
    kemuyi_seen: { q1: 1 },
    kemuyi_new_session: null
  };
  const { context, storage } = createApp({ storage: seed });
  const before = new Map(storage);
  assert.throws(() => context.window.__KMY__.importBackupObject({ kemuyi_sm2: "{broken" }));
  assert.deepStrictEqual(Array.from(storage.entries()), Array.from(before.entries()));
}

testLegacyImportAndSeenInference();
testRemoteDebugDataWrapperImport();
testVersionTwoMerge();
testInvalidImportIsAtomic();
console.log("record transfer tests passed");
