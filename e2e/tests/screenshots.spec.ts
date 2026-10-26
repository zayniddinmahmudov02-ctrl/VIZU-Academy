import { test } from "@playwright/test";

// Not an assertion suite: saves screenshots for a visual review (E2E_SHOTS=1).
test.skip(!process.env.E2E_SHOTS, "set E2E_SHOTS=1 to capture review screenshots");

for (const path of ["/", "/login", "/register"]) {
  test(`shot ${path}`, async ({ page }, info) => {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const name = path === "/" ? "welcome" : path.slice(1);
    await page.screenshot({ path: `shots/${info.project.name}-${name}.png`, fullPage: true });
    if (path !== "/") {
      await page.getByRole("button", { name: "Hilfe" }).click();
      await page.screenshot({ path: `shots/${info.project.name}-${name}-help.png` });
    }
  });
}
