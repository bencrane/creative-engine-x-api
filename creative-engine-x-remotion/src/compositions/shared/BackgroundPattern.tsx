import React from "react";
import { AbsoluteFill } from "remotion";
import type { Brand } from "../../schemas/inputProps";

export type BackgroundStyle = "gradient" | "solid" | "dark-gradient" | "accent-top";

interface BackgroundPatternProps {
  brand: Brand;
  style?: BackgroundStyle;
  children: React.ReactNode;
  padding?: number;
}

function getBackground(brand: Brand, bgStyle: BackgroundStyle): string {
  switch (bgStyle) {
    case "gradient":
      return `linear-gradient(135deg, ${brand.primary_color} 0%, ${brand.secondary_color} 100%)`;
    case "dark-gradient":
      return `linear-gradient(180deg, ${brand.secondary_color} 0%, ${brand.primary_color}33 100%)`;
    case "solid":
      return brand.secondary_color;
    case "accent-top":
      return brand.secondary_color;
  }
}

export const BackgroundPattern: React.FC<BackgroundPatternProps> = ({
  brand,
  style: bgStyle = "gradient",
  children,
  padding = 60,
}) => {
  return (
    <AbsoluteFill
      style={{
        background: getBackground(brand, bgStyle),
        justifyContent: "center",
        alignItems: "center",
        padding,
      }}
    >
      {bgStyle === "accent-top" && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            background: brand.primary_color,
          }}
        />
      )}
      {children}
    </AbsoluteFill>
  );
};
