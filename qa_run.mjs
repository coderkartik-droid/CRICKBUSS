export default async function run(page) {
  const BASE = "http://127.0.0.1:8765";
  const VIEWPORTS = [320, 375, 390, 768, 1024, 1366];
  const PAGES = [
    ["/", "Home"],
    ["/accounts/login/", "Login"],
    ["/accounts/signup/", "Signup"],
    ["/dashboard/", "Dashboard"],
    ["/dashboard/admin-portal/", "Admin Portal"],
    ["/dashboard/managed-users/", "Managed Users"],
    ["/dashboard/profile/", "Profile"],
    ["/dashboard/profile/edit/", "Profile Edit"],
    ["/dashboard/notifications/settings/", "Notif Settings"],
    ["/dashboard/local/teams/", "Teams Admin"],
    ["/dashboard/local/players/", "Players Admin"],
    ["/dashboard/local/grounds/", "Grounds Admin"],
    ["/dashboard/local/matches/", "Matches Admin"],
    ["/dashboard/local/tournaments/", "Tournaments Admin"],
    ["/dashboard/local/venue/", "Venues Admin"],
    ["/dashboard/local/series/", "Series Admin"],
    ["/dashboard/local/news/", "News Admin"],
    ["/matches/", "Matches Public"],
    ["/teams/", "Teams Public"],
    ["/players/", "Players Public"],
    ["/series/", "Series Public"],
    ["/news/", "News Public"],
    ["/gallery/", "Gallery Public"],
    ["/videos/", "Videos Public"],
    ["/contact/", "Contact"],
  ];

  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto(BASE + "/accounts/login/", { waitUntil: "domcontentloaded" });
  await page.fill('input[name="username"]', "chaudharysavita588@gmail.com");
  await page.fill('input[name="password"]', "QA_Test2026!");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("domcontentloaded");

  const results = {};
  const consoleErrors = [];
  const failedReqs = [];
  page.on("console", m => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 120)); });
  page.on("response", r => {
    if (r.status() >= 400 && !r.url().includes("favicon")) failedReqs.push(r.status() + " " + r.url().slice(-80));
  });

  for (const vp of VIEWPORTS) {
    await page.setViewportSize({ width: vp, height: 900 });
    for (const [path, name] of PAGES) {
      const key = `${name}@${vp}`;
      try {
        await page.goto(BASE + path, { waitUntil: "domcontentloaded", timeout: 15000 });
        await page.waitForTimeout(350);
        const issues = await page.evaluate(() => {
          const res = { overflowX: false, offscreen: [], overlaps: [], brokenImgs: [], invisibleText: [] };
          const vw = window.innerWidth;
          const de = document.documentElement;
          if (de.scrollWidth > vw + 2) res.overflowX = `doc ${de.scrollWidth} > vw ${vw}`;
          // buttons offscreen
          document.querySelectorAll(".btn, button").forEach(b => {
            if (!b.offsetParent) return;
            const r = b.getBoundingClientRect();
            if (r.width === 0) return;
            if (r.right > vw + 4 || r.left < -4) res.offscreen.push((b.textContent || b.getAttribute("aria-label") || "").trim().slice(0, 22) + " L" + Math.round(r.left) + " R" + Math.round(r.right));
          });
          // overlaps
          const btns = [...document.querySelectorAll(".btn, button")].filter(b => b.offsetParent);
          for (let i = 0; i < btns.length; i++) for (let j = i + 1; j < btns.length; j++) {
            if (btns[i].contains(btns[j]) || btns[j].contains(btns[i])) continue;
            const a = btns[i].getBoundingClientRect(), b = btns[j].getBoundingClientRect();
            if (!a.width || !b.width) continue;
            const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            if (ox > 6 && oy > 6) res.overlaps.push(((btns[i].textContent || "?").trim().slice(0, 15)) + "||" + ((btns[j].textContent || "?").trim().slice(0, 15)));
          }
          // broken images
          document.querySelectorAll("img").forEach(im => {
            if (im.complete && im.naturalWidth === 0 && im.src) res.brokenImgs.push(im.src.slice(-60));
          });
          // dark-on-dark / light-on-light quick heuristic for buttons
          document.querySelectorAll(".btn, button").forEach(b => {
            if (!b.offsetParent) return;
            const bs = getComputedStyle(b);
            const bg = bs.backgroundColor, fg = bs.color;
            const parse = c => c.match(/\d+/g).map(Number);
            if (!bg || bg === "transparent" || !fg) return;
            try {
              const [r1, g1, b1] = parse(bg), [r2, g2, b2] = parse(fg);
              const lum = (r, g, bl) => (0.2126 * r + 0.7152 * g + 0.072 * bl);
              const d = Math.abs(lum(r1, g1, b1) - lum(r2, g2, b2));
              if (d < 40 && (b.textContent || "").trim()) res.invisibleText.push((b.textContent.trim().slice(0, 20)) + " bg" + bg + " fg" + fg);
            } catch (e) { }
          });
          res.offscreen = [...new Set(res.offscreen)].slice(0, 5);
          res.overlaps = [...new Set(res.overlaps)].slice(0, 5);
          res.brokenImgs = [...new Set(res.brokenImgs)].slice(0, 3);
          res.invisibleText = [...new Set(res.invisibleText)].slice(0, 5);
          return res;
        });
        const bad = [];
        if (issues.overflowX) bad.push("OVERFLOW: " + issues.overflowX);
        if (issues.offscreen.length) bad.push("OFFSCREEN: " + issues.offscreen.join(" | "));
        if (issues.overlaps.length) bad.push("OVERLAP: " + issues.overlaps.join(" | "));
        if (issues.brokenImgs.length) bad.push("BROKEN-IMG: " + issues.brokenImgs.join(","));
        if (issues.invisibleText.length) bad.push("LOW-CONTRAST: " + issues.invisibleText.join(" | "));
        if (bad.length) results[key] = bad;
      } catch (e) {
        results[key] = ["NAV-ERROR: " + String(e).slice(0, 100)];
      }
    }
  }
  results._consoleErrors = [...new Set(consoleErrors)].slice(0, 10);
  results._failedRequests = [...new Set(failedReqs)].slice(0, 15);
  if (!Object.keys(results).filter(k => !k.startsWith("_")).length) results._summary = "ALL CLEAN";
  return results;
}
