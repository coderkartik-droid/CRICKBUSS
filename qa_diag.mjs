export default async function run(page) {
  const BASE = "http://127.0.0.1:8765";
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(BASE + "/accounts/login/", { waitUntil: "domcontentloaded" });
  await page.fill('input[name="username"]', "chaudharysavita588@gmail.com");
  await page.fill('input[name="password"]', "QA_Test2026!");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("domcontentloaded");
  const out = {};
  for (const [name, url, w] of [["dash320", "/dashboard/", 320], ["admin375", "/dashboard/admin-portal/", 375], ["mu1366", "/dashboard/managed-users/", 1366], ["dash768", "/dashboard/", 768]]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    out[name] = await page.evaluate(() => {
      const res = [];
      const vw = window.innerWidth;
      document.querySelectorAll(".btn, button").forEach(b => {
        if (!b.offsetParent) return;
        const r = b.getBoundingClientRect();
        if (r.right > vw + 4 || r.left < -4) {
          const chain = [];
          let el = b;
          for (let i = 0; i < 4 && el; i++) { chain.push(el.tagName + "." + String(el.className).slice(0, 60)); el = el.parentElement; }
          res.push({ btn: (b.textContent || "").trim().slice(0, 20), chain, rect: [Math.round(r.left), Math.round(r.right), Math.round(r.width)] });
        }
      });
      return res;
    });
  }
  return out;
}
