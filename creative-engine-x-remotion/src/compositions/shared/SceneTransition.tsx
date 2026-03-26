import React from "react";
import {
  TransitionSeries,
  linearTiming,
  springTiming,
} from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import type { TransitionPresentation } from "@remotion/transitions";
import type { Scene, Brand } from "../../schemas/inputProps";
import { FPS } from "../../schemas/inputProps";

export type TransitionStyle = "fade" | "slide" | "wipe" | "slide-up";

interface SceneTransitionProps {
  scenes: Scene[];
  brand: Brand;
  ctaDurationSeconds?: number;
  transitionDurationFrames?: number;
  transitionStyle?: TransitionStyle;
  useSpringTiming?: boolean;
  renderScene: (scene: Scene, index: number) => React.ReactNode;
  renderCTA: () => React.ReactNode;
}

function getPresentation(style: TransitionStyle): TransitionPresentation<Record<string, unknown>> {
  switch (style) {
    case "fade":
      return fade();
    case "slide":
      return slide({ direction: "from-right" });
    case "slide-up":
      return slide({ direction: "from-bottom" });
    case "wipe":
      return wipe({ direction: "from-left" });
  }
}

export const SceneTransition: React.FC<SceneTransitionProps> = ({
  scenes,
  ctaDurationSeconds = 3,
  transitionDurationFrames = 10,
  transitionStyle = "fade",
  useSpringTiming = false,
  renderScene,
  renderCTA,
}) => {
  const presentation = getPresentation(transitionStyle);

  const timing = useSpringTiming
    ? springTiming({ durationInFrames: transitionDurationFrames })
    : linearTiming({ durationInFrames: transitionDurationFrames });

  return (
    <TransitionSeries>
      {scenes.map((scene, i) => (
        <React.Fragment key={i}>
          {i > 0 && (
            <TransitionSeries.Transition
              timing={timing}
              presentation={presentation}
            />
          )}
          <TransitionSeries.Sequence
            durationInFrames={Math.round(scene.duration_seconds * FPS)}
          >
            {renderScene(scene, i)}
          </TransitionSeries.Sequence>
        </React.Fragment>
      ))}
      <TransitionSeries.Transition
        timing={timing}
        presentation={presentation}
      />
      <TransitionSeries.Sequence
        durationInFrames={ctaDurationSeconds * FPS}
      >
        {renderCTA()}
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
