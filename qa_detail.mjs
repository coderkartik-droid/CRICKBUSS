export default async function run(page) {
  const BASE = "http://127.0.0.1:8765";
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(BASE + "/accounts/login/", { waitUntil: "domcontentloaded" });
  await page.fill('input[name="username"]', "chaudharysavita588@gmail.com");
  await page.fill('input[name="password"]', "QA_Test2026!");
  await page.click('.content-card button[type="submit"]');
  await page.waitForLoadState("domcontentloaded");
  const out = {};
  for (const [name, url, w] of [["dash320", "/dashboard/", 320], ["admin375", "/dashboard/admin-portal/", 375], ["mu768", "/dashboard/managed-users/", 768], ["nav1366", "/", 1366], ["nav1024", "/", 1024], ["nav768", "/", 768], ["nav320", "/", 320]]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    out[name] = await page.evaluate(() => {
      const res = { offscreen: [], overlaps: [] };
      const vw = window.innerWidth;
      document.querySelectorAll(".btn, button, a.badge").forEach(b => {
        if (!b.offsetParent) return;
        const r = b.getBoundingClientRect();
        if (r.right > vw + 4 || r.left < -4) res.offscreen.push((b.textContent || "").trim().slice(0, 25) + " [" + String(b.className).slice(0, 40) + "] L" + Math.round(r.left) + " R" + Math.round(r.right) + " vw" + vw);
      });
      const btns = [...document.querySelectorAll(".btn, button, a.badge")].filter(b => b.offsetParent);
      for (let i = 0; i < btns.length; i++) for (let j = i + 1; j < btns.length; j++) {
        const a = btns[i].getBoundingClientRect(), b = btns[j].getBoundingClientRect();
        if (!a.width || !b.width || btns[i].contains(btns[j]) || btns[j].contains(btns[i])) continue;
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox > 6 && oy > 6) res.overlaps.push((btns[i].textContent || "").trim().slice(0, 15) + "||" + (btns[j].textContent || "").trim().slice(0, 15) + " [" + String(btns[j].className).slice(0, 40) + "]");
      }
      res.offscreen = [...new Set(res.offscreen)].slice(0, 8);
      res.overlaps = [...new Set(res.overlaps)].slice(0, 6);
      return res;
    });
  }
  return out;
}
