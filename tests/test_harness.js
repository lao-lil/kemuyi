const fs = require("fs");
const vm = require("vm");

class FakeClassList {
  constructor() { this.values = new Set(); }
  add(name) { this.values.add(name); }
  remove(name) { this.values.delete(name); }
  contains(name) { return this.values.has(name); }
  toggle(name, force) {
    const enabled = force === undefined ? !this.values.has(name) : force;
    if (enabled) this.values.add(name);
    else this.values.delete(name);
    return enabled;
  }
}

class FakeElement {
  constructor(id) {
    this.id = id;
    this.classList = new FakeClassList();
    this.style = {};
    this.children = [];
    this.disabled = false;
    this.textContent = "";
    this.value = "";
    this.files = [];
    this.onclick = null;
    this.onchange = null;
    this._innerHTML = "";
    this.clicked = false;
  }

  set innerHTML(value) {
    this._innerHTML = value;
    if (this.id === "q-area") {
      this.children = Array.from(value.matchAll(/class="opt[^"]*" data-i="(\d+)"/g), (match) => {
        const option = new FakeElement("option-" + match[1]);
        option.dataIndex = match[1];
        option.getAttribute = (name) => name === "data-i" ? option.dataIndex : null;
        return option;
      });
    } else if (this.id === "sheet-grid") {
      this.children = Array.from(value.matchAll(/data-i="(\d+)"/g), (match) => {
        const item = new FakeElement("sheet-" + match[1]);
        item.dataIndex = match[1];
        item.getAttribute = (name) => name === "data-i" ? item.dataIndex : null;
        return item;
      });
    }
  }

  get innerHTML() { return this._innerHTML; }
  querySelectorAll(selector) { return selector === ".opt" ? this.children : []; }
  setAttribute(name, value) { this[name] = value; }
  getAttribute(name) { return this[name] || null; }
  click() {
    this.clicked = true;
    if (this.onclick) this.onclick();
  }
}

function createApp(options = {}) {
  const elements = {};
  const document = {
    getElementById(id) {
      if (!elements[id]) elements[id] = new FakeElement(id);
      return elements[id];
    },
    createElement(tag) {
      const el = new FakeElement(tag);
      return el;
    }
  };
  const initialStorage = options.storage || {};
  const storage = new Map(Object.entries(initialStorage).map(([key, value]) => [
    key,
    typeof value === "string" ? value : JSON.stringify(value)
  ]));
  const localStorage = {
    getItem(key) { return storage.has(key) ? storage.get(key) : null; },
    setItem(key, value) { storage.set(key, String(value)); },
    removeItem(key) { storage.delete(key); }
  };
  const alerts = [];
  const confirms = [];
  const downloads = [];
  class FakeFileReader {
    readAsText(file) {
      this.result = file.content;
      if (this.onload) this.onload();
    }
  }
  class FakeBlob {
    constructor(parts, blobOptions) {
      this.text = parts.join("");
      this.type = blobOptions && blobOptions.type;
    }
  }
  const math = Object.create(Math);
  math.random = options.random || (() => 0.5);
  const window = {
    __BANK__: options.bank || [
      { id: "q1", type: "single", category: "law", question: "题目一", options: ["正确", "错误"], answer: 0 },
      { id: "q2", type: "single", category: "law", question: "题目二", options: ["正确", "错误"], answer: 0 }
    ],
    scrollTo() {},
    addEventListener() {},
    URL: {
      createObjectURL(blob) {
        downloads.push(blob);
        return "blob:test";
      },
      revokeObjectURL() {}
    },
    console
  };
  const context = {
    window,
    document,
    localStorage,
    navigator: {},
    FileReader: FakeFileReader,
    Blob: FakeBlob,
    URL: window.URL,
    confirm(message) {
      confirms.push(message);
      return options.confirmResult !== false;
    },
    alert(message) { alerts.push(message); },
    console,
    Date,
    Math: math,
    JSON,
    Object,
    Array,
    String,
    parseInt,
    setInterval() { return { fakeInterval: true }; },
    clearInterval() {},
    setTimeout,
    clearTimeout
  };
  vm.runInNewContext(
    fs.readFileSync(require.resolve("../src/app.js"), "utf8"),
    context,
    { filename: "src/app.js" }
  );
  return { elements, storage, alerts, confirms, downloads, context };
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = { createApp, wait };
