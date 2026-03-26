import { describe, it, expect } from "vitest";

// Test that composition modules export the expected components
// (We can't render React components in vitest without jsdom, but we can verify exports)

describe("MetaAd composition", () => {
  it("exports MetaAd component", async () => {
    const mod = await import("../src/compositions/MetaAd");
    expect(mod.MetaAd).toBeDefined();
    expect(typeof mod.MetaAd).toBe("function");
  });
});

describe("TikTokAd composition", () => {
  it("exports TikTokAd component", async () => {
    const mod = await import("../src/compositions/TikTokAd");
    expect(mod.TikTokAd).toBeDefined();
    expect(typeof mod.TikTokAd).toBe("function");
  });
});

describe("GenericVideo composition", () => {
  it("exports GenericVideo component", async () => {
    const mod = await import("../src/compositions/GenericVideo");
    expect(mod.GenericVideo).toBeDefined();
    expect(typeof mod.GenericVideo).toBe("function");
  });
});

describe("Root component", () => {
  it("exports RemotionRoot component", async () => {
    // RemotionRoot imports from remotion which requires browser env,
    // so we just check the file is importable
    const mod = await import("../src/Root");
    expect(mod.RemotionRoot).toBeDefined();
    expect(typeof mod.RemotionRoot).toBe("function");
  });
});
