import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import {
  TransitionSeries,
  linearTiming,
} from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import type { VideoInputProps } from "../schemas/inputProps";
import { FPS } from "../schemas/inputProps";

const GenericScene: React.FC<{
  text: string;
  visualDirection: string;
  brand: VideoInputProps["brand"];
}> = ({ text, brand }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" },
  );
  const opacity = Math.min(fadeIn, fadeOut);

  const yOffset = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 100 },
  });

  return (
    <AbsoluteFill
      style={{
        background: brand.secondary_color,
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
      }}
    >
      {/* Accent bar */}
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

      <div
        style={{
          color: "#FFFFFF",
          fontSize: 44,
          fontWeight: 600,
          fontFamily: brand.font_family || "Inter, sans-serif",
          textAlign: "center",
          lineHeight: 1.4,
          opacity,
          transform: `translateY(${interpolate(yOffset, [0, 1], [30, 0])}px)`,
        }}
      >
        {text}
      </div>

      {/* Brand footer */}
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
    </AbsoluteFill>
  );
};

const GenericCTA: React.FC<{
  ctaText: string;
  brand: VideoInputProps["brand"];
}> = ({ ctaText, brand }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 150 },
  });

  const buttonScale = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 180 },
    delay: 10,
  });

  return (
    <AbsoluteFill
      style={{
        background: brand.secondary_color,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
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
            fontSize: 36,
            fontWeight: 700,
            fontFamily: brand.font_family || "Inter, sans-serif",
            padding: "20px 48px",
            borderRadius: 12,
            transform: `scale(${buttonScale})`,
          }}
        >
          {ctaText}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const GenericVideo: React.FC<VideoInputProps> = ({
  scenes,
  brand,
  cta_text,
}) => {
  const CTA_DURATION_SECONDS = 3;
  const transitionDuration = 15; // Smooth, professional transitions

  return (
    <AbsoluteFill>
      <TransitionSeries>
        {scenes.map((scene, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <TransitionSeries.Transition
                timing={linearTiming({ durationInFrames: transitionDuration })}
                presentation={fade()}
              />
            )}
            <TransitionSeries.Sequence
              durationInFrames={Math.round(scene.duration_seconds * FPS)}
            >
              <GenericScene
                text={scene.text}
                visualDirection={scene.visual_direction}
                brand={brand}
              />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
        <TransitionSeries.Transition
          timing={linearTiming({ durationInFrames: transitionDuration })}
          presentation={fade()}
        />
        <TransitionSeries.Sequence
          durationInFrames={CTA_DURATION_SECONDS * FPS}
        >
          <GenericCTA ctaText={cta_text} brand={brand} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
