import React from "react";
import type { Brand } from "../../schemas/inputProps";

export type BrandBarPosition = "top" | "bottom";

interface BrandBarProps {
  brand: Brand;
  position?: BrandBarPosition;
  showLogo?: boolean;
  opacity?: number;
  fontSize?: number;
}

export const BrandBar: React.FC<BrandBarProps> = ({
  brand,
  position = "bottom",
  showLogo = true,
  opacity = 0.7,
  fontSize = 20,
}) => {
  const isTop = position === "top";

  return (
    <div
      style={{
        position: "absolute",
        [isTop ? "top" : "bottom"]: 40,
        left: 40,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      {showLogo && brand.logo_url && (
        <img
          src={brand.logo_url}
          alt={brand.company_name}
          style={{ height: fontSize * 1.6, objectFit: "contain" }}
        />
      )}
      <div
        style={{
          color: `rgba(255,255,255,${opacity})`,
          fontSize,
          fontFamily: brand.font_family || "Inter, sans-serif",
          fontWeight: 500,
        }}
      >
        {brand.company_name}
      </div>
    </div>
  );
};
