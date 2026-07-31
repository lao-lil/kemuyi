const assert = require("assert");
const { createApp } = require("./test_harness");

const { elements, storage } = createApp({
  storage: {
    kemuyi_sm2: { q1: {} },
    kemuyi_wrong: { q1: {} },
    kemuyi_stats: { totalAnswered: 1 },
    kemuyi_seen: { q1: 1 },
    kemuyi_new_session: { version: 1 }
  }
});
elements["btn-reset"].onclick();
["kemuyi_sm2", "kemuyi_wrong", "kemuyi_stats", "kemuyi_seen", "kemuyi_new_session"].forEach((key) => {
  assert.strictEqual(storage.has(key), false, `重置后仍存在 ${key}`);
});
console.log("reset progress tests passed");
