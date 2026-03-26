import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import type { VideoInputProps } from "../schemas/inputProps";
import type { Scene } from "../schemas/inputProps";
import { TextOverlay } from "./shared/TextOverlay";
import { CTASlide } from "./shared/CTASlide";
import { SceneTransition } from "./shared/SceneTransition";
import { BackgroundPattern } from "./shared/BackgroundPattern";

const GenericScene: React.FC<{
  scene: Scene;
  brand: VideoInputProps["brand"];
}> = ({ scene, brand }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" },
  );
  const sceneOpacity = Math.min(fadeIn, fadeOut);

  return (
    <BackgroundPattern brand={brand} style="accent-top" padding={80}>
      <div style={{ opacity: sceneOpacity }}>
        <TextOverlay
          text={scene.text}
          brand={brand}
          variant="clean"
          fontSize={44}
          fontWeight={600}
        />
      </div>

      {/* Brand footer with dot */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: brand.primary_color,
          }}
        />
        <div
          style={{
            color: "rgba(255,255,255,0.6)",
            fontSize: 18,
            fontFamily: brand.font_family || "Inter, sans-serif",
          }}
        >
          {brand.company_name}
        </div>
      </div>
    </BackgroundPattern>
  );
};

export const GenericVideo: React.FC<VideoInputProps> = ({
  scenes,
  brand,
  cta_text,
}) => {
  return (
    <AbsoluteFill>
      <SceneTransition
        scenes={scenes}
        brand={brand}
        transitionStyle="fade"
        transitionDurationFrames={15}
        renderScene={(scene) => <GenericScene scene={scene} brand={brand} />}
        renderCTA={() => (
          <CTASlide ctaText={cta_text} brand={brand} variant="professional" />
        )}
      />
    </AbsoluteFill>
  );
};
