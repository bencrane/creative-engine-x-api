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
import { slide } from "@remotion/transitions/slide";
import type { VideoInputProps } from "../schemas/inputProps";
import { FPS } from "../schemas/inputProps";

const TikTokScene: React.FC<{
  text: string;
  visualDirection: string;
  brand: VideoInputProps["brand"];
}> = ({ text, brand }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 180 },
  });

  const captionOpacity = interpolate(frame, [5, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${brand.secondary_color} 0%, ${brand.primary_color}33 100%)`,
        justifyContent: "center",
        alignItems: "center",
        padding: 40,
      }}
    >
      {/* Main text */}
      <div
        style={{
          color: "#FFFFFF",
          fontSize: 52,
          fontWeight: 800,
          fontFamily: brand.font_family || "Inter, sans-serif",
          textAlign: "center",
          lineHeight: 1.2,
          transform: `translateY(${interpolate(entrance, [0, 1], [60, 0])}px)`,
          opacity: entrance,
        }}
      >
        {text}
      </div>

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
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const TikTokCTA: React.FC<{
  ctaText: string;
  brand: VideoInputProps["brand"];
}> = ({ ctaText, brand }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  const bounce = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 200 },
    delay: 3,
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
          fontSize: 60,
          fontWeight: 900,
          fontFamily: brand.font_family || "Inter, sans-serif",
          textAlign: "center",
          transform: `scale(${bounce})`,
          padding: 40,
        }}
      >
        {ctaText}
      </div>
      <div
        style={{
          position: "absolute",
          bottom: height * 0.08,
          color: "rgba(255,255,255,0.6)",
          fontSize: 18,
          fontFamily: brand.font_family || "Inter, sans-serif",
        }}
      >
        @{brand.company_name.toLowerCase().replace(/\s+/g, "")}
      </div>
    </AbsoluteFill>
  );
};

export const TikTokAd: React.FC<VideoInputProps> = ({
  scenes,
  brand,
  cta_text,
}) => {
  const CTA_DURATION_SECONDS = 3;
  const transitionDuration = 6; // Quick cuts for TikTok

  return (
    <AbsoluteFill>
      <TransitionSeries>
        {scenes.map((scene, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <TransitionSeries.Transition
                timing={linearTiming({ durationInFrames: transitionDuration })}
                presentation={slide({ direction: "from-bottom" })}
              />
            )}
            <TransitionSeries.Sequence
              durationInFrames={Math.round(scene.duration_seconds * FPS)}
            >
              <TikTokScene
                text={scene.text}
                visualDirection={scene.visual_direction}
                brand={brand}
              />
            </TransitionSeries.Sequence>
          </React.Fragment>
        ))}
        <TransitionSeries.Transition
          timing={linearTiming({ durationInFrames: transitionDuration })}
          presentation={slide({ direction: "from-bottom" })}
        />
        <TransitionSeries.Sequence
          durationInFrames={CTA_DURATION_SECONDS * FPS}
        >
          <TikTokCTA ctaText={cta_text} brand={brand} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
