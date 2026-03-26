import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import type { Brand } from "../../schemas/inputProps";

export type TextOverlayVariant = "bold" | "caption" | "clean";

interface TextOverlayProps {
  text: string;
  brand: Brand;
  variant?: TextOverlayVariant;
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  textAlign?: React.CSSProperties["textAlign"];
}

const variantConfig: Record<
  TextOverlayVariant,
  { damping: number; stiffness: number; translateY: number; fadeFrames: number }
> = {
  bold: { damping: 15, stiffness: 120, translateY: 40, fadeFrames: 15 },
  caption: { damping: 18, stiffness: 180, translateY: 60, fadeFrames: 10 },
  clean: { damping: 20, stiffness: 100, translateY: 30, fadeFrames: 20 },
};

export const TextOverlay: React.FC<TextOverlayProps> = ({
  text,
  brand,
  variant = "clean",
  fontSize,
  fontWeight,
  color = "#FFFFFF",
  textAlign = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const config = variantConfig[variant];

  const entrance = spring({
    frame,
    fps,
    config: { damping: config.damping, stiffness: config.stiffness },
  });

  const opacity = interpolate(frame, [0, config.fadeFrames], [0, 1], {
    extrapolateRight: "clamp",
  });

  const defaultFontSize = variant === "bold" ? 52 : variant === "caption" ? 22 : 44;
  const defaultFontWeight = variant === "bold" ? 800 : variant === "caption" ? 500 : 600;

  return (
    <div
      style={{
        color,
        fontSize: fontSize ?? defaultFontSize,
        fontWeight: fontWeight ?? defaultFontWeight,
        fontFamily: brand.font_family || "Inter, sans-serif",
        textAlign,
        lineHeight: 1.3,
        opacity,
        transform: `translateY(${interpolate(entrance, [0, 1], [config.translateY, 0])}px)`,
      }}
    >
      {text}
    </div>
  );
};
