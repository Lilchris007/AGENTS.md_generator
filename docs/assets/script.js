(() => {
  const btn = document.querySelector("[data-copy-target]");
  if (!btn) return;

  const targetSel = btn.getAttribute("data-copy-target");
  if (!targetSel) return;

  const target = document.querySelector(targetSel);
  if (!target) return;

  const getText = () => {
    const code = target.querySelector("code");
    return (code ? code.textContent : target.textContent) || "";
  };

  btn.addEventListener("click", async () => {
    const text = getText().trimEnd();
    try {
      await navigator.clipboard.writeText(text + "\n");
      const prev = btn.textContent;
      btn.textContent = "Copied";
      window.setTimeout(() => (btn.textContent = prev), 900);
    } catch {
      // Best-effort fallback. No UI spam.
    }
  });
})();

