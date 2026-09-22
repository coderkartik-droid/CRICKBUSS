export default async function run(page) {
  const BASE = "http://127.0.0.1:8765";
  const WIDTHS = [320, 375, 390, 768, 1024, 1366];

  // ---- Login ----
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(BASE + "/accounts/login/", { waitUntil: "domcontentloaded" });
  await page.fill('input[name="username"]', "chaudharysavita588@gmail.com");
  await page.fill('input[name="password"]', "QA_Test2026!");
  await page.click('.content-card button[type="submit"]');
  await page.waitForLoadState("domcontentloaded");
  const loggedIn = await page.evaluate(() => !!document.querySelector('.dropdown-toggle img') || !document.querySelector('a[href*="login"]'));
  if (!loggedIn) return { error: "login failed" };

  const pages = [
    "/dashboard/", "/dashboard/super-admin/", "/dashboard/scorer/", "/dashboard/admin-portal/",
    "/dashboard/managed-users/", "/dashboard/website-settings/", "/dashboard/saved/",
    "/dashboard/notifications/", "/dashboard/my-comments/",
    "/accounts/profile/",
    "/dashboard/local/match/", "/dashboard/local/team/", "/dashboard/local/player/",
    "/dashboard/local/ground/", "/dashboard/local/tournament/",
    "/teams/", "/players/", "/series/", "/news/", "/videos/", "/photos/", "/rankings/",
    "/matches/", "/contact/", "/about/",
  ];

  const issues = [];
  const pagesTested = [];
  const failedRequests = new Set();
  const consoleErrors = new Set();
  page.on("response", r => { if (r.status() >= 400) failedRequests.add(r.status() + " " + r.url().slice(0, 100)); });
  page.on("console", m => { if (m.type() === "error") consoleErrors.add(m.text().slice(0, 120)); });

  async function audit(url, width) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(350);
    return page.evaluate(() => {
      const out = { horiz: false, overlaps: [], offscreenBtns: 0, tinyBtns: [], brokenImgs: [] };
      const doc = document.scrollingElement;
      out.horiz = doc.scrollWidth > window.innerWidth + 2;
      const vw = window.innerWidth;
      // overlapping visible buttons
      const btns = [...document.querySelectorAll(".btn, button, a.badge")].filter(b => b.offsetParent);
      for (let i = 0; i < btns.length; i++) {
        for (let j = i + 1; j < btns.length; j++) {
          const a = btns[i].getBoundingClientRect(), b = btns[j].getBoundingClientRect();
          if (!a.width || !b.width) continue;
          if (btns[i].contains(btns[j]) || btns[j].contains(btns[i])) continue;
          const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          if (ox > 6 && oy > 6) out.overlaps.push(String(btns[i].className).slice(0, 30) + "||" + String(btns[j].className).slice(0, 30));
        }
      }
      out.overlaps = [...new Set(out.overlaps)].slice(0, 5);
      // offscreen / overflow buttons
      btns.forEach(b => { const r = b.getBoundingClientRect(); if (r.right > vw + 4 || r.left < -4) out.offscreenBtns++; });
      // tiny touch targets
      btns.forEach(b => { const r = b.getBoundingClientRect(); if (r.height > 0 && r.height < 30) out.tinyBtns.push(String(b.className).slice(0, 30)); });
      out.tinyBtns = [...new Set(out.tinyBtns)].slice(0, 5);
      // broken images
      document.querySelectorAll("img").forEach(im => { if (im.complete && im.naturalWidth === 0 && im.src && !im.src.startsWith("data:")) out.brokenImgs.push(im.src.split("/").pop().slice(0, 40)); });
      out.brokenImgs = [...new Set(out.brokenImgs)].slice(0, 4);
      return out;
    });
  }

  for (const url of pages) {
    const perWidth = {};
    let anyIssue = false;
    for (const w of WIDTHS) {
      const r = await audit(url, w);
      perWidth[w] = r;
      if (r.horiz || r.overlaps.length || r.offscreenBtns || r.brokenImgs.length) anyIssue = true;
    }
    pagesTested.push(url);
    if (anyIssue) issues.push({ url, perWidth });
  }
  return { pagesTestedCount: pagesTested.length, issues, failedRequests: [...failedRequests], consoleErrors: [...consoleErrors].slice(0, 10) };
}
