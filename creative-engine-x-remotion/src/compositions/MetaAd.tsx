import React from "react";
import { AbsoluteFill } from "remotion";
import type { VideoInputProps } from "../schemas/inputProps";
import type { Scene } from "../schemas/inputProps";
import { TextOverlay } from "./shared/TextOverlay";
import { BrandBar } from "./shared/BrandBar";
import { CTASlide } from "./shared/CTASlide";
import { SceneTransition } from "./shared/SceneTransition";
import { BackgroundPattern } from "./shared/BackgroundPattern";

const MetaScene: React.FC<{
  scene: Scene;
  brand: VideoInputProps["brand"];
}> = ({ scene, brand }) => {
  return (
    <BackgroundPattern brand={brand} style="gradient" padding={60}>
      <TextOverlay
        text={scene.text}
        brand={brand}
        variant="bold"
        fontSize={48}
        fontWeight={700}
      />
      <BrandBar brand={brand} position="bottom" opacity={0.7} />
    </BackgroundPattern>
  );
};

export const MetaAd: React.FC<VideoInputProps> = ({
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
        transitionDurationFrames={10}
        renderScene={(scene) => <MetaScene scene={scene} brand={brand} />}
        renderCTA={() => <CTASlide ctaText={cta_text} brand={brand} variant="bold" />}
      />
    </AbsoluteFill>
  );
};
