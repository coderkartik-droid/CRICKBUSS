export default async function run(page) {
  const BASE = "http://127.0.0.1:8765";
  const out = {};
  for (const w of [320, 375, 390, 768, 1024]) {
    await page.setViewportSize({ width: w, height: 844 });
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    await page.click(".navbar-toggler");
    await page.waitForTimeout(500);
    const r = await page.evaluate(() => {
      const panel = document.querySelector(".navbar-collapse");
      if (!panel || !panel.classList.contains("show")) return { error: "panel not open" };
      const pr = panel.getBoundingClientRect();
      const nav = document.querySelector(".navbar-custom").getBoundingClientRect();
      const items = [...panel.querySelectorAll(".nav-link-custom")].map(a => {
        const icon = a.querySelector(".nav-item-icon");
        const text = a.querySelector("span");
        const ir = icon.getBoundingClientRect(), tr = text.getBoundingClientRect(), ar = a.getBoundingClientRect();
        return {
          text: text.textContent.trim(),
          h: Math.round(ar.height),
          gapPx: Math.round(tr.left - ir.right),
          iconLeftAligned: Math.round(ir.left - ar.left),
          sameRow: Math.abs(ir.top - tr.top) < 5,
          fullStretch: ar.width > window.innerWidth * 0.95,
        };
      });
      return {
        panelRect: { top: Math.round(pr.top), navBottom: Math.round(nav.bottom), width: Math.round(pr.width), left: Math.round(pr.left), right: Math.round(pr.right) },
        panelRightBelowNavbar: pr.top >= nav.bottom - 4,
        vw: window.innerWidth,
        items,
        horizScroll: document.documentElement.scrollWidth > window.innerWidth + 2,
      };
    });
    out["w" + w] = r;
    await page.screenshot({ path: `C:\\Users\\hari1\\CRICKBUSS\\qa_nav_${w}.png` });
    await page.keyboard.press("Escape");
    await page.click("body", { position: { x: 5, y: 300 } }).catch(() => { });
    await page.waitForTimeout(400);
    out["w" + w].closedAfterOutsideClick = await page.evaluate(() => !document.querySelector(".navbar-collapse").classList.contains("show"));
    // close on link click
    await page.click(".navbar-toggler");
    await page.waitForTimeout(500);
    const openNow = await page.evaluate(() => document.querySelector(".navbar-collapse").classList.contains("show"));
    if (openNow) {
      await page.click(".navbar-collapse .nav-link-custom");
      await page.waitForTimeout(500);
    }
    out["w" + w].closedAfterLinkClick = await page.evaluate(() => !document.querySelector(".navbar-collapse").classList.contains("show"));
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded" });
  }
  return out;
}
