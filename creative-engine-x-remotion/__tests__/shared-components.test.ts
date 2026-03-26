import { describe, it, expect } from "vitest";

describe("shared/TextOverlay", () => {
  it("exports TextOverlay component", async () => {
    const mod = await import("../src/compositions/shared/TextOverlay");
    expect(mod.TextOverlay).toBeDefined();
    expect(typeof mod.TextOverlay).toBe("function");
  });
});

describe("shared/BrandBar", () => {
  it("exports BrandBar component", async () => {
    const mod = await import("../src/compositions/shared/BrandBar");
    expect(mod.BrandBar).toBeDefined();
    expect(typeof mod.BrandBar).toBe("function");
  });
});

describe("shared/CTASlide", () => {
  it("exports CTASlide component", async () => {
    const mod = await import("../src/compositions/shared/CTASlide");
    expect(mod.CTASlide).toBeDefined();
    expect(typeof mod.CTASlide).toBe("function");
  });
});

describe("shared/SceneTransition", () => {
  it("exports SceneTransition component", async () => {
    const mod = await import("../src/compositions/shared/SceneTransition");
    expect(mod.SceneTransition).toBeDefined();
    expect(typeof mod.SceneTransition).toBe("function");
  });
});

describe("shared/BackgroundPattern", () => {
  it("exports BackgroundPattern component", async () => {
    const mod = await import("../src/compositions/shared/BackgroundPattern");
    expect(mod.BackgroundPattern).toBeDefined();
    expect(typeof mod.BackgroundPattern).toBe("function");
  });
});

describe("shared/index barrel", () => {
  it("re-exports all shared components", async () => {
    const mod = await import("../src/compositions/shared/index");
    expect(mod.TextOverlay).toBeDefined();
    expect(mod.BrandBar).toBeDefined();
    expect(mod.CTASlide).toBeDefined();
    expect(mod.SceneTransition).toBeDefined();
    expect(mod.BackgroundPattern).toBeDefined();
  });
});
