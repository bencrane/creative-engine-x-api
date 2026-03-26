import { describe, it, expect } from "vitest";
import {
  videoInputPropsSchema,
  sceneSchema,
  brandSchema,
  defaultProps,
  calculateTotalDurationInFrames,
  FPS,
} from "../src/schemas/inputProps";

describe("sceneSchema", () => {
  it("accepts valid scene", () => {
    const scene = {
      text: "Hello world",
      visual_direction: "Wide shot",
      duration_seconds: 5,
    };
    expect(sceneSchema.parse(scene)).toEqual(scene);
  });

  it("rejects scene with duration < 1", () => {
    expect(() =>
      sceneSchema.parse({
        text: "Hello",
        visual_direction: "Wide",
        duration_seconds: 0,
      }),
    ).toThrow();
  });

  it("rejects scene with duration > 60", () => {
    expect(() =>
      sceneSchema.parse({
        text: "Hello",
        visual_direction: "Wide",
        duration_seconds: 61,
      }),
    ).toThrow();
  });

  it("rejects scene missing text", () => {
    expect(() =>
      sceneSchema.parse({ visual_direction: "Wide", duration_seconds: 5 }),
    ).toThrow();
  });
});

describe("brandSchema", () => {
  it("accepts valid brand with all fields", () => {
    const brand = {
      primary_color: "#FF0000",
      secondary_color: "#000000",
      company_name: "Test Co",
      logo_url: "https://example.com/logo.png",
      font_family: "Helvetica",
    };
    expect(brandSchema.parse(brand)).toEqual(brand);
  });

  it("applies defaults for missing optional fields", () => {
    const brand = brandSchema.parse({});
    expect(brand.primary_color).toBe("#0066FF");
    expect(brand.secondary_color).toBe("#09090b");
    expect(brand.company_name).toBe("Company");
  });

  it("allows optional logo_url and font_family", () => {
    const brand = brandSchema.parse({
      primary_color: "#FF0000",
      secondary_color: "#000000",
      company_name: "Test",
    });
    expect(brand.logo_url).toBeUndefined();
    expect(brand.font_family).toBeUndefined();
  });
});

describe("videoInputPropsSchema", () => {
  it("accepts valid full props", () => {
    const result = videoInputPropsSchema.parse(defaultProps);
    expect(result.scenes).toHaveLength(3);
    expect(result.brand.company_name).toBe("Creative Engine X");
    expect(result.cta_text).toBe("Start Free Trial →");
  });

  it("rejects empty scenes array", () => {
    expect(() =>
      videoInputPropsSchema.parse({
        ...defaultProps,
        scenes: [],
      }),
    ).toThrow();
  });

  it("applies default cta_text", () => {
    const result = videoInputPropsSchema.parse({
      scenes: [
        { text: "Hello", visual_direction: "Wide", duration_seconds: 3 },
      ],
      brand: { company_name: "Test" },
    });
    expect(result.cta_text).toBe("Learn More");
  });
});

describe("calculateTotalDurationInFrames", () => {
  it("calculates correct duration from scenes", () => {
    const scenes = [
      { text: "A", visual_direction: "V", duration_seconds: 4 },
      { text: "B", visual_direction: "V", duration_seconds: 4 },
      { text: "C", visual_direction: "V", duration_seconds: 3 },
    ];
    // (4 + 4 + 3 + 3 CTA) * 30 = 420
    expect(calculateTotalDurationInFrames(scenes)).toBe(420);
  });

  it("uses default 3s CTA duration", () => {
    const scenes = [
      { text: "A", visual_direction: "V", duration_seconds: 10 },
    ];
    // (10 + 3) * 30 = 390
    expect(calculateTotalDurationInFrames(scenes)).toBe(390);
  });

  it("accepts custom CTA duration", () => {
    const scenes = [
      { text: "A", visual_direction: "V", duration_seconds: 10 },
    ];
    // (10 + 5) * 30 = 450
    expect(calculateTotalDurationInFrames(scenes, 5)).toBe(450);
  });

  it("rounds up fractional frames", () => {
    const scenes = [
      { text: "A", visual_direction: "V", duration_seconds: 3.5 },
    ];
    // (3.5 + 3) * 30 = 195
    expect(calculateTotalDurationInFrames(scenes)).toBe(195);
  });

  it("FPS constant is 30", () => {
    expect(FPS).toBe(30);
  });
});

describe("defaultProps", () => {
  it("has 3 scenes", () => {
    expect(defaultProps.scenes).toHaveLength(3);
  });

  it("all scenes have required fields", () => {
    for (const scene of defaultProps.scenes) {
      expect(scene.text).toBeTruthy();
      expect(scene.visual_direction).toBeTruthy();
      expect(scene.duration_seconds).toBeGreaterThan(0);
    }
  });

  it("validates against schema", () => {
    expect(() => videoInputPropsSchema.parse(defaultProps)).not.toThrow();
  });
});
