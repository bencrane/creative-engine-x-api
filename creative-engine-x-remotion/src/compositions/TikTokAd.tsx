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

const TikTokScene: React.FC<{
  scene: Scene;
  brand: VideoInputProps["brand"];
}> = ({ scene, brand }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();

  const captionOpacity = interpolate(frame, [5, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <BackgroundPattern brand={brand} style="dark-gradient" padding={40}>
      <TextOverlay
        text={scene.text}
        brand={brand}
        variant="caption"
        fontSize={52}
        fontWeight={800}
      />

      {/* Caption bar at bottom */}
      <div
        style={{
          position: "absolute",
          bottom: height * 0.12,
          left: 24,
          right: 24,
          background: "rgba(0,0,0,0.7)",
          borderRadius: 12,
          padding: "16px 24px",
          opacity: captionOpacity,
        }}
      >
        <div
          style={{
            color: "#FFFFFF",
            fontSize: 22,
            fontFamily: brand.font_family || "Inter, sans-serif",
            fontWeight: 500,
            textAlign: "center",
          }}
        >
          {scene.text}
        </div>
      </div>
    </BackgroundPattern>
  );
};

export const TikTokAd: React.FC<VideoInputProps> = ({
  scenes,
  brand,
  cta_text,
}) => {
  return (
    <AbsoluteFill>
      <SceneTransition
        scenes={scenes}
        brand={brand}
        transitionStyle="slide-up"
        transitionDurationFrames={6}
        renderScene={(scene) => <TikTokScene scene={scene} brand={brand} />}
        renderCTA={() => <CTASlide ctaText={cta_text} brand={brand} variant="bouncy" />}
      />
    </AbsoluteFill>
  );
};
