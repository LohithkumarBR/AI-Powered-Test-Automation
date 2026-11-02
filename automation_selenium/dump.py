Find_element_by_ff_js_script = """
  const target = arguments[0];
  const callback = arguments[arguments.length - 1];

  const MAX_WAIT = 2000;
  const INTERVAL = 50;
  const start = Date.now();

  // ---------------- FINDER ----------------
  function findByFfInspect(root) {
      const visited = new Set();
      const stack = [{ node: root, frames: [] }];

      while (stack.length > 0) {
          const { node, frames } = stack.pop();
          if (!node) continue;

          if (
              node.nodeType === Node.DOCUMENT_NODE ||
              node.nodeType === Node.DOCUMENT_FRAGMENT_NODE
          ) {
              if (visited.has(node)) continue;
              visited.add(node);
          }

          if (node.nodeType === Node.ELEMENT_NODE) {

              if (node.getAttribute && node.getAttribute("ff-inspect") === target) {
                  return { node, frames };
              }

              // Shadow DOM
              if (node.shadowRoot) {
                  stack.push({ node: node.shadowRoot, frames });
              }

              // Iframe traversal
              if (node.tagName === "IFRAME") {
                try {
                    const doc = node.contentDocument || node.contentWindow?.document;
                    if (doc) {
                        const meta = {
                            id: node.id || null,
                            name: node.getAttribute("name") || null,
                            title: node.getAttribute("title") || null,
                            aria: node.getAttribute("aria-label") || null,
                            src: node.getAttribute("src") || null,
                        };

                        stack.push({
                            node: doc,
                            frames: [...frames, meta]
                        });
                    }
                } catch (e) {}
              }

              const kids = node.children || node.childNodes;
              for (let i = kids.length - 1; i >= 0; i--) {
                  stack.push({ node: kids[i], frames });
              }
          }

          else if (
              node.nodeType === Node.DOCUMENT_NODE ||
              node.nodeType === Node.DOCUMENT_FRAGMENT_NODE
          ) {
              const kids = node.childNodes;
              for (let i = kids.length - 1; i >= 0; i--) {
                  stack.push({ node: kids[i], frames });
              }
          }
      }

      return null;
  }

  // ---------------- CLICKABILITY ----------------
  function isClickable(el) {
      if (!el || el.nodeType !== Node.ELEMENT_NODE) return false;
      const tag = el.tagName.toLowerCase();
      if (tag === "button" || tag === "a") return true;
      if (el.getAttribute("role") === "button") return true;
      if (tag === "input") {
          const t = (el.getAttribute("type") || "").toLowerCase();
          return t === "button" || t === "submit";
      }
      return false;
  }

  function findClickableInside(root) {
      const queue = [root];
      while (queue.length) {
          const node = queue.shift();
          if (isClickable(node)) return node;
          const kids = node.children || node.childNodes;
          for (let k of kids) queue.push(k);
      }
      return null;
  }

  // ---------------- XPATH BUILDER ----------------
  function buildXPath(el) {
      if (!el) return null;

      if (el.id) return `//*[@id="${el.id}"]`;

      const name = el.getAttribute("name");
      if (name) return `//*[@name="${name}"]`;

      const text = el.textContent && el.textContent.trim();
      if (text && text.length < 50) {
          const escaped = text.replace(/"/g, '\\"');
          const xp = `//*[text()="${escaped}"]`;
          try {
              const n = document.evaluate(xp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
              if (n.singleNodeValue === el) return xp;
          } catch {}
      }

      const parts = [];
      let node = el;

      while (node && node.nodeType === Node.ELEMENT_NODE) {
          let idx = 1;
          let sib = node.previousSibling;
          while (sib) {
              if (sib.nodeType === Node.ELEMENT_NODE && sib.nodeName === node.nodeName) idx++;
              sib = sib.previousSibling;
          }
          parts.unshift(node.nodeName.toLowerCase() + "[" + idx + "]");
          node = node.parentNode instanceof ShadowRoot ? node.parentNode.host : node.parentNode;
      }

      return "/" + parts.join("/");
  }

  // ---------------- WAIT LOOP ----------------
  (function attempt() {
      const found = findByFfInspect(document);

      if (!found) {
          if (Date.now() - start > MAX_WAIT) {
              return callback({ success: false, reason: "timeout" });
          }
          return setTimeout(attempt, INTERVAL);
      }

      let targetNode = found.node;
      if (!isClickable(targetNode)) {
          const inside = findClickableInside(targetNode);
          if (inside) targetNode = inside;
      }

      const xpath = buildXPath(targetNode);

      return callback({
          success: true,
          xpath,
          frames: found.frames
      });
  })();

"""


# INJECT_AND_SERIALIZE_DOM_JS = r"""
# return (function () {

#   let nodeIndex = 0;

#   // ==========================================================
#   //  ACCURATE COVERAGE CHECK (Improved)
#   // ==========================================================
#   function getCoverageStatus(el) {

#     if (!el || !el.getBoundingClientRect) return "unknown";

#     const rect = el.getBoundingClientRect();
#     if (rect.width === 0 || rect.height === 0) return "false";

#     const testPoints = [
#       [rect.left + 5, rect.top + 5],
#       [rect.right - 5, rect.top + 5],
#       [rect.left + 5, rect.bottom - 5],
#       [rect.right - 5, rect.bottom - 5],
#       [rect.left + rect.width / 2, rect.top + rect.height / 2]
#     ];

#     for (let [x, y] of testPoints) {

#       let topEl = document.elementFromPoint(x, y);
#       if (!topEl) continue;

#       if (topEl === el || el.contains(topEl)) continue;

#       const style = getComputedStyle(topEl);

#       if (
#         style.pointerEvents === "none" ||
#         style.opacity === "0" ||
#         style.visibility === "hidden"
#       ) {
#         continue;
#       }

#       if (el.closest("label")?.contains(topEl)) continue;
#       if (topEl.closest("label")?.contains(el)) continue;
#       if (el.parentElement && el.parentElement.contains(topEl)) continue;

#       const isBlocking =
#         ["BUTTON", "A"].includes(topEl.tagName) ||
#         topEl.onclick ||
#         topEl.getAttribute("role") === "button";

#       if (isBlocking) return "true";
#     }

#     return "false";
#   }

#   // ==========================================================
#   //  INTERACTIVITY METADATA
#   // ==========================================================
#   function annotateInteractivity(el) {

#     const s = getComputedStyle(el);

#     el.setAttribute("element-visibility", s.visibility || "");
#     el.setAttribute("element-pointer-events", s.pointerEvents || "");
#     el.setAttribute("element-zindex", s.zIndex || "");

#     try {
#       el.setAttribute("element-covered", getCoverageStatus(el));
#     } catch {
#       el.setAttribute("element-covered", "unknown");
#     }
#   }

#   // ==========================================================
#   //  FULL XPATH + SHADOW PATH BUILDER (INDEXED)
#   // ==========================================================
#   function getXPath(node) {

#     if (!node || node.nodeType !== 1) return "";

#     if (node === document.documentElement) return "/html";

#     let parent = node.parentNode;

#     // ==================================================
#     // Shadow Root Case (WITH INDEX)
#     // ==================================================
#     if (parent instanceof ShadowRoot) {

#       const hostPath = getXPath(parent.host);

#       const siblings = Array.from(parent.children)
#         .filter(n => n.tagName === node.tagName);

#       const idx = siblings.indexOf(node) + 1;

#       return (
#         hostPath +
#         "/shadow/" +
#         node.tagName.toLowerCase() +
#         "[" + idx + "]"
#       );
#     }

#     // ==================================================
#     // Normal DOM Indexing
#     // ==================================================
#     const siblings = Array.from(parent.children)
#       .filter(n => n.tagName === node.tagName);

#     const index = siblings.indexOf(node) + 1;

#     return (
#       getXPath(parent) +
#       "/" +
#       node.tagName.toLowerCase() +
#       "[" + index + "]"
#     );
#   }

#   // ==========================================================
#   //  PROCESS NODE (Inject Everything)
#   // ==========================================================
#   function processNode(node) {

#     if (!node || node.nodeType !== 1) return;

#     //if (node.hasAttribute("ff-inspect")) return;

#     node.setAttribute("ff-inspect", `Fire-Flink-${nodeIndex++}`);
#     node.setAttribute("ff-xpath", getXPath(node));

#     annotateInteractivity(node);

#     if (node.shadowRoot) {
#       node.shadowRoot.querySelectorAll("*").forEach(processNode);
#     }

#     if (node.tagName === "IFRAME") {
#       try {
#         const doc = node.contentDocument;
#         if (doc) {
#           doc.querySelectorAll("*").forEach(processNode);
#         }
#       } catch {
#         node.setAttribute("ff-cross-origin", "true");
#       }
#     }

#     node.querySelectorAll(":scope > *").forEach(processNode);
#   }

#   // ==========================================================
#   //  INITIAL FULL PAGE INJECTION
#   // ==========================================================
#   document.querySelectorAll("*").forEach(processNode);

#   // ==========================================================
#   //  MUTATION OBSERVER (React / SPA Fix)
#   // ==========================================================
#   const observer = new MutationObserver(mutations => {

#     for (const mutation of mutations) {

#       mutation.addedNodes.forEach(node => {

#         if (node.nodeType === 1) {
#           processNode(node);
#           node.querySelectorAll("*").forEach(processNode);
#         }

#       });

#     }
#   });

#   observer.observe(document.body, {
#     childList: true,
#     subtree: true
#   });

#   // ==========================================================
#   //  FULL DOM SERIALIZER (DOM + Shadow + iframe)
#   // ==========================================================
#   function serializeNode(node) {

#     if (node.nodeType === Node.TEXT_NODE) {
#       return node.textContent;
#     }

#     if (node.nodeType !== Node.ELEMENT_NODE) return "";

#     const tag = node.tagName.toLowerCase();
#     let html = `<${tag}`;

#     for (const attr of node.attributes) {
#       html += ` ${attr.name}="${attr.value.replace(/"/g, "&quot;")}"`;
#     }

#     html += ">";

#     if (node.shadowRoot) {
#       html += "<!--#shadow-root-open-->";
#       node.shadowRoot.querySelectorAll("*").forEach(child => {
#         html += serializeNode(child);
#       });
#       html += "<!--#/shadow-root-->";
#     }

#     if (tag === "iframe" && node.getAttribute("ff-cross-origin") !== "true") {
#       try {
#         const doc = node.contentDocument;
#         if (doc) {
#           html += "<!--#iframe-content-->";
#           html += serializeNode(doc.documentElement);
#           html += "<!--#/iframe-content-->";
#         }
#       } catch {}
#     }

#     for (const child of node.childNodes) {
#       html += serializeNode(child);
#     }

#     html += `</${tag}>`;

#     return html;
#   }

#   return "<!DOCTYPE html>\n" + serializeNode(document.documentElement);

# })();
# """
INJECT_AND_SERIALIZE_DOM_JS = r"""
return (function () {

  let nodeIndex = 0;

  // ==========================================================
  // COVERAGE CHECK
  // ==========================================================
    function getCoverageStatus(el) {

    if (!el || !el.getBoundingClientRect) return "unknown";

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return "false";

    const testPoints = [
      [rect.left + 5, rect.top + 5],
      [rect.right - 5, rect.top + 5],
      [rect.left + 5, rect.bottom - 5],
      [rect.right - 5, rect.bottom - 5],
      [rect.left + rect.width / 2, rect.top + rect.height / 2]
    ];

    for (let [x, y] of testPoints) {

      let topEl = document.elementFromPoint(x, y);
      if (!topEl) continue;

      if (topEl === el || el.contains(topEl)) continue;

      const style = getComputedStyle(topEl);

      if (
        style.pointerEvents === "none" ||
        style.opacity === "0" ||
        style.visibility === "hidden"
      ) {
        continue;
      }

      if (el.closest("label")?.contains(topEl)) continue;
      if (topEl.closest("label")?.contains(el)) continue;
      if (el.parentElement && el.parentElement.contains(topEl)) continue;

      const isBlocking =
        ["BUTTON", "A"].includes(topEl.tagName) ||
        topEl.onclick ||
        topEl.getAttribute("role") === "button";

      if (isBlocking) return "true";
    }

    return "false";
  }

function isUsable(node) {
  const s = getComputedStyle(node);

  if (
    s.display === "none" ||
    s.visibility === "hidden" ||
    s.opacity === "0" ||
    s.pointerEvents === "none"
  ) {
    return false;
  }

  const rect = node.getBoundingClientRect();

  if (rect.width === 0 || rect.height === 0) {
    return false;
  }

  return true;
}

  function annotate(node) {
    const s = getComputedStyle(node);

    node.setAttribute("element-visibility", s.visibility || "");
    node.setAttribute("element-pointer-events", s.pointerEvents || "");
    node.setAttribute("element-zindex", s.zIndex || "");

     if (!isUsable(node)) {
    node.setAttribute("element-covered", "true");
    return;
  }
    
    try {
      node.setAttribute("element-covered", getCoverageStatus(node));
    } catch {
      node.setAttribute("element-covered", "unknown");
    }
  }

  // ==========================================================
  // XPATH (Shadow + iframe safe)
  // ==========================================================

  function getXPath(node) {

  if (!node || node.nodeType !== 1) return "";

  let segments = [];
  let current = node;

  // ============================================
  // Build Local DOM Path (Bottom → Top)
  // ============================================
  while (current && current.nodeType === 1) {

    const parent = current.parentNode;

    // Shadow Root Case
    if (parent instanceof ShadowRoot) {

      const host = parent.host;

      const siblings = Array.from(parent.children)
        .filter(n => n.tagName === current.tagName);

      const index = siblings.indexOf(current) + 1;

      segments.unshift(
        "shadow/" +
        current.tagName.toLowerCase() +
        "[" + index + "]"
      );

      current = host;
      continue;
    }

    let index = 1;

    if (parent && parent.children) {
      const siblings = Array.from(parent.children)
        .filter(n => n.tagName === current.tagName);

      index = siblings.indexOf(current) + 1;
    }

    segments.unshift(
      current.tagName.toLowerCase() + "[" + index + "]"
    );

    if (!parent || parent.nodeType !== 1) break;

    current = parent;
  }

  let path = "/" + segments.join("/");

  // ============================================
  // If inside iframe → prefix iframe path
  // ============================================
  if (node.ownerDocument !== document) {

    const frameEl =
      node.ownerDocument.defaultView &&
      node.ownerDocument.defaultView.frameElement;

    if (frameEl) {

      let framePath = frameEl.getAttribute("ff-xpath");

      if (!framePath) {
        framePath = getXPath(frameEl);
      }

      path = framePath + path;
    }
  }

  return path;
}

  

  // ==========================================================
  // TRUE NODE-BY-NODE WALK (TreeWalker)
  // ==========================================================
  function walk(root) {

    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_ELEMENT,
      null,
      false
    );

    let node = walker.currentNode;

    while (node) {

      if (
          node.nodeType === 1 &&
          !["META", "STYLE", "SCRIPT"].includes(node.tagName)
        ) {

        node.setAttribute(
          "ff-inspect",
          "Fire-Flink-" + nodeIndex++
        );

        node.setAttribute(
          "ff-xpath",
          getXPath(node)
        );

        annotate(node);
      }

      // Shadow DOM
      if (node.shadowRoot) {
        walk(node.shadowRoot);
      }

      // Same-origin iframe
      if (node.tagName === "IFRAME") {
        try {
          const doc = node.contentDocument;
          if (doc && doc.documentElement) {
            walk(doc.documentElement);
          }
        } catch {
          node.setAttribute("ff-cross-origin", "true");
        }
      }

      node = walker.nextNode();
    }
  }

  // Start traversal
  walk(document.documentElement);

  // ==========================================================
  // SERIALIZER
  // ==========================================================
  function serializeNode(node) {

    if (node.nodeType === Node.TEXT_NODE)
      return node.textContent;

    if (node.nodeType !== Node.ELEMENT_NODE)
      return "";

    const tag = node.tagName.toLowerCase();
    let html = "<" + tag;

    for (const attr of node.attributes) {
      if (attr.name === "srcdoc") continue;

      html += " " + attr.name +
        "=\"" +
        attr.value.replace(/"/g, "&quot;") +
        "\"";
    }

    html += ">";

    if (node.shadowRoot) {
      html += "<!--#shadow-root-->";
      node.shadowRoot.childNodes.forEach(child => {
        html += serializeNode(child);
      });
      html += "<!--#/shadow-root-->";
    }

    if (tag === "iframe" &&
        node.getAttribute("ff-cross-origin") !== "true") {
      try {
        const doc = node.contentDocument;
        if (doc) {
          html += serializeNode(doc.documentElement);
        }
      } catch {}
    }

    node.childNodes.forEach(child => {
      html += serializeNode(child);
    });

    html += "</" + tag + ">";
    return html;
  }

  return "<!DOCTYPE html>\n" +
         serializeNode(document.documentElement);

})();
"""


TOAST_WATCHER_JS = r"""
(function () {

  // --- STOP any old watcher first ---
  if (window.__toastObserver) {
    try { window.__toastObserver.disconnect(); } catch(e) {}
  }

  // --- Reset state for this step ---
  window.__toastDetected = false;
  window.__lastToastText = null;

  function isVisible(el) {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 &&
           s.display !== "none" &&
           s.visibility !== "hidden" &&
           s.opacity !== "0";
  }

  const observer = new MutationObserver(muts => {
    for (const m of muts) {

      // New elements
      for (const node of m.addedNodes || []) {
        if (node.nodeType !== 1) continue;
        const text = node.innerText?.trim();
        if (!text || text.length < 3 || text.length > 300) continue;
        if (!isVisible(node)) continue;

        window.__toastDetected = true;
        window.__lastToastText = text;
        return;
      }

      // Text changes
      if (m.type === "characterData") {
        const el = m.target.parentElement;
        if (!el) continue;
        const text = el.innerText?.trim();
        if (!text || text.length < 3 || text.length > 300) continue;
        if (!isVisible(el)) continue;

        window.__toastDetected = true;
        window.__lastToastText = text;
        return;
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });

  window.__toastObserver = observer;
})();
"""

SHADOW_DOM_CLICK_JS = r"""
const path = arguments[0];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\w+)\[(\d+)\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");
  let node = document.evaluate(parts[0], document, null,
      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

  for (let i=1; i<parts.length; i++) {
    node = node.shadowRoot.querySelector(toCss(parts[i].replace(/\//g, " > ")));
  }

  return node;
}

const targetNode = resolve(path);
if (targetNode) {
    targetNode.click();
    return true;
}
return false;
"""

SHADOW_DOM_ENTER_JS = r"""
const path = arguments[0];
const value = arguments[1];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\w+)\[(\d+)\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");
  let node = document.evaluate(parts[0], document, null,
      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

  for (let i=1; i<parts.length; i++) {
    node = node.shadowRoot.querySelector(toCss(parts[i].replace(/\//g, " > ")));
  }

  return node;
}

const el = resolve(path);
if (el) {
    el.focus();
    el.value = "";
    el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
}
return false;

"""

SHADOW_DOM_UPLOAD_JS = r"""
const path = arguments[0];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\w+)\[(\d+)\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");
  let node = document.evaluate(parts[0], document, null,
      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

  for (let i=1; i<parts.length; i++) {
    node = node.shadowRoot.querySelector(toCss(parts[i].replace(/\//g, " > ")));
  }

  return node;
}

return resolve(path);
"""

SHADOW_DOM_GET_TEXT_JS = """
const path = arguments[0];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\\w+)\\[(\\d+)\\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");

  let node = document.evaluate(
    parts[0],
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  ).singleNodeValue;

  for (let i = 1; i < parts.length; i++) {
    if (!node || !node.shadowRoot) return null;
    node = node.shadowRoot.querySelector(
      toCss(parts[i].replace(/\\//g, " > "))
    );
  }

  return node;
}

const el = resolve(path);
return el ? el.innerText.trim() : null;
"""
SHADOW_DOM_VERIFY_TEXT_JS = """
const path = arguments[0];
const text = arguments[1];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\\w+)\\[(\\d+)\\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");

  let node = document.evaluate(
    parts[0],
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  ).singleNodeValue;

  for (let i = 1; i < parts.length; i++) {
    if (!node || !node.shadowRoot) return null;
    node = node.shadowRoot.querySelector(
      toCss(parts[i].replace(/\\//g, " > "))
    );
  }

  return node;
}

const el = resolve(path);
return el ? el.innerText.trim() == text : false;
"""
SHADOW_DOM_VERIFY_PARTIAL_TEXT_JS = """
const path = arguments[0];
const text = arguments[1];

function resolve(path) {

  function toCss(sel) {
    return sel.replace(/(\\w+)\\[(\\d+)\\]/g,
      (_, t, n) => `${t}:nth-of-type(${n})`);
  }

  const parts = path.split("/shadow/");

  let node = document.evaluate(
    parts[0],
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  ).singleNodeValue;

  for (let i = 1; i < parts.length; i++) {
    if (!node || !node.shadowRoot) return null;
    node = node.shadowRoot.querySelector(
      toCss(parts[i].replace(/\\//g, " > "))
    );
  }

  return node;
}

const el = resolve(path);
return el ? el.innerText.trim().includes(text) : false;
"""