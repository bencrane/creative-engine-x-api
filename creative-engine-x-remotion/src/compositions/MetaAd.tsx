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

const SceneSlide: React.FC<{
  text: string;
  visualDirection: string;
  brand: VideoInputProps["brand"];
}> = ({ text, brand }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const textEntrance = spring({ frame, fps, config: { damping: 15, stiffness: 120 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${brand.primary_color} 0%, ${brand.secondary_color} 100%)`,
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
      }}
    >
      <div
        style={{
          color: "#FFFFFF",
          fontSize: 48,
          fontWeight: 700,
          fontFamily: brand.font_family || "Inter, sans-serif",
          textAlign: "center",
          lineHeight: 1.3,
          opacity,
          transform: `translateY(${interpolate(textEntrance, [0, 1], [40, 0])}px)`,
        }}
      >
        {text}
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: 40,
          color: "rgba(255,255,255,0.7)",
          fontSize: 20,
          fontFamily: brand.font_family || "Inter, sans-serif",
          fontWeight: 500,
        }}
      >
        {brand.company_name}
      </div>
    </AbsoluteFill>
  );
};

const CTASlide: React.FC<{
  ctaText: string;
  brand: VideoInputProps["brand"];
}> = ({ ctaText, brand }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 200 },
    delay: 5,
  });

  return (
    <AbsoluteFill
      style={{
        background: brand.primary_color,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          color: "#FFFFFF",
          fontSize: 56,
          fontWeight: 800,
          fontFamily: brand.font_family || "Inter, sans-serif",
          textAlign: "center",
          transform: `scale(${scale})`,
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
        {brand.company_name}
      </div>
    </AbsoluteFill>
  );
};

export const MetaAd: React.FC<VideoInputProps> = ({
  scenes,
  brand,
  cta_text,
}) => {
  const CTA_DURATION_SECONDS = 3;
  const transitionDuration = 10; // frames

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
              <SceneSlide
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
          <CTASlide ctaText={cta_text} brand={brand} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
