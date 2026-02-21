(() => {
  const STORAGE_KEY = "agentsmd_style_v1";
  const root = document.documentElement;

  const normalizeStyle = (value) => (value === "ascii" ? "ascii" : "default");

  const getStoredStyle = () => {
    try {
      return normalizeStyle(localStorage.getItem(STORAGE_KEY));
    } catch {
      return "default";
    }
  };

  const setStoredStyle = (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {}
  };

  const makeBox = (text) => {
    const label = String(text || "").replace(/\s+/g, " ").trim();
    const inner = `  ${label}  `;
    const top = `┌${"─".repeat(inner.length)}┐`;
    const mid = `│${inner}│`;
    const bot = `└${"─".repeat(inner.length)}┘`;
    return `${top}\n${mid}\n${bot}`;
  };

  const stickerNodes = Array.from(document.querySelectorAll("[data-ascii-sticker]"));
  for (const node of stickerNodes) {
    if (!node.dataset.asciiOriginalHtml) {
      node.dataset.asciiOriginalHtml = node.innerHTML;
    }
  }

  const renderStickers = (style) => {
    const ascii = style === "ascii";
    for (const node of stickerNodes) {
      const label = (node.getAttribute("data-ascii-sticker") || "").trim();
      if (!label) continue;

      if (ascii) {
        node.innerHTML = "";
        const pre = document.createElement("pre");
        pre.className = "ascii-sticker";
        pre.textContent = makeBox(label);
        pre.setAttribute("aria-label", label);
        node.appendChild(pre);
      } else {
        node.innerHTML = node.dataset.asciiOriginalHtml || label;
      }
    }
  };

  const syncButtons = (style) => {
    const buttons = Array.from(document.querySelectorAll("[data-style-value]"));
    for (const btn of buttons) {
      const pressed = btn.getAttribute("data-style-value") === style;
      btn.setAttribute("aria-pressed", pressed ? "true" : "false");
    }
  };

  const applyStyle = (style) => {
    const next = normalizeStyle(style);
    root.dataset.style = next;
    setStoredStyle(next);
    renderStickers(next);
    syncButtons(next);
  };

  const init = () => {
    const initial = normalizeStyle(root.dataset.style || getStoredStyle());
    applyStyle(initial);

    const buttons = Array.from(document.querySelectorAll("[data-style-value]"));
    for (const btn of buttons) {
      btn.addEventListener("click", () => {
        const value = normalizeStyle(btn.getAttribute("data-style-value"));
        applyStyle(value);
      });
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
