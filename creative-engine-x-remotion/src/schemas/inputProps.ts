import { z } from "zod";

export const sceneSchema = z.object({
  text: z.string(),
  visual_direction: z.string(),
  duration_seconds: z.number().min(1).max(60),
});

export const brandSchema = z.object({
  primary_color: z.string().default("#0066FF"),
  secondary_color: z.string().default("#09090b"),
  company_name: z.string().default("Company"),
  logo_url: z.string().optional(),
  font_family: z.string().optional(),
});

export const videoInputPropsSchema = z.object({
  scenes: z.array(sceneSchema).min(1),
  brand: brandSchema,
  cta_text: z.string().default("Learn More"),
  music_url: z.string().optional(),
});

export type VideoInputProps = z.infer<typeof videoInputPropsSchema>;
export type Scene = z.infer<typeof sceneSchema>;
export type Brand = z.infer<typeof brandSchema>;

export const FPS = 30;

export const defaultProps: VideoInputProps = {
  scenes: [
    {
      text: "Transform your business with AI-powered creative automation",
      visual_direction: "Bold text on gradient background, modern tech aesthetic",
      duration_seconds: 4,
    },
    {
      text: "Generate videos, ads, and content in seconds — not hours",
      visual_direction: "Split screen showing before/after workflow comparison",
      duration_seconds: 4,
    },
    {
      text: "Trusted by 500+ marketing teams worldwide",
      visual_direction: "Social proof with company logos and testimonials",
      duration_seconds: 3,
    },
  ],
  brand: {
    primary_color: "#0066FF",
    secondary_color: "#09090b",
    company_name: "Creative Engine X",
    font_family: "Inter, sans-serif",
  },
  cta_text: "Start Free Trial →",
};

export function calculateTotalDurationInFrames(
  scenes: Scene[],
  ctaDurationSeconds: number = 3,
): number {
  const sceneDuration = scenes.reduce(
    (sum, scene) => sum + scene.duration_seconds,
    0,
  );
  return Math.ceil((sceneDuration + ctaDurationSeconds) * FPS);
}
