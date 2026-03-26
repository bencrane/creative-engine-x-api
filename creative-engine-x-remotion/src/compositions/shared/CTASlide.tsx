import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import type { Brand } from "../../schemas/inputProps";

export type CTAVariant = "bold" | "bouncy" | "professional";

interface CTASlideProps {
  ctaText: string;
  brand: Brand;
  variant?: CTAVariant;
}

const ctaConfig: Record<
  CTAVariant,
  { damping: number; stiffness: number; delay: number; fontSize: number; fontWeight: number }
> = {
  bold: { damping: 12, stiffness: 200, delay: 5, fontSize: 56, fontWeight: 800 },
  bouncy: { damping: 8, stiffness: 200, delay: 3, fontSize: 60, fontWeight: 900 },
  professional: { damping: 10, stiffness: 180, delay: 10, fontSize: 36, fontWeight: 700 },
};

export const CTASlide: React.FC<CTASlideProps> = ({
  ctaText,
  brand,
  variant = "bold",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const config = ctaConfig[variant];

  const scale = spring({
    frame,
    fps,
    config: { damping: config.damping, stiffness: config.stiffness },
    delay: config.delay,
  });

  const entrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 150 },
  });

  return (
    <AbsoluteFill
      style={{
        background:
          variant === "professional" ? brand.secondary_color : brand.primary_color,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {variant === "professional" ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 32,
            opacity: entrance,
            transform: `translateY(${interpolate(entrance, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              color: "#FFFFFF",
              fontSize: 32,
              fontWeight: 400,
              fontFamily: brand.font_family || "Inter, sans-serif",
            }}
          >
            {brand.company_name}
          </div>
          <div
            style={{
              background: brand.primary_color,
              color: "#FFFFFF",
              fontSize: config.fontSize,
              fontWeight: config.fontWeight,
              fontFamily: brand.font_family || "Inter, sans-serif",
              padding: "20px 48px",
              borderRadius: 12,
              transform: `scale(${scale})`,
            }}
          >
            {ctaText}
          </div>
        </div>
      ) : (
        <>
          <div
            style={{
              color: "#FFFFFF",
              fontSize: config.fontSize,
              fontWeight: config.fontWeight,
              fontFamily: brand.font_family || "Inter, sans-serif",
              textAlign: "center",
              transform: `scale(${scale})`,
              padding: 40,
            }}
          >
            {ctaText}
          </div>
          <div
            style={{
              position: "absolute",
              bottom: 60,
              color: "rgba(255,255,255,0.8)",
              fontSize: 24,
              fontFamily: brand.font_family || "Inter, sans-serif",
            }}
          >
            {variant === "bouncy"
              ? `@${brand.company_name.toLowerCase().replace(/\s+/g, "")}`
              : brand.company_name}
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};
