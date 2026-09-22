export default async function run(page) {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("http://127.0.0.1:8765/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);
  return await page.evaluate(() => {
    const t = document.querySelector(".navbar-toggler");
    const wrap = t.parentElement;
    const brand = document.querySelector(".navbar-brand-custom");
    const cs = getComputedStyle(t);
    const r = t.getBoundingClientRect();
    return {
      togglerRect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
      wrapRect: JSON.stringify(wrap.getBoundingClientRect()),
      brandRect: JSON.stringify(brand.getBoundingClientRect()),
      wrapClass: wrap.className,
    };
  });
}
