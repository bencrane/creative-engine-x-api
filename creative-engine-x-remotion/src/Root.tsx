import React from "react";
import { Composition } from "remotion";
import {
  videoInputPropsSchema,
  defaultProps,
  calculateTotalDurationInFrames,
  FPS,
  type VideoInputProps,
} from "./schemas/inputProps";
import { MetaAd } from "./compositions/MetaAd";
import { TikTokAd } from "./compositions/TikTokAd";
import { GenericVideo } from "./compositions/GenericVideo";

const calculateMetadata = ({
  props,
}: {
  props: VideoInputProps;
}) => {
  return {
    durationInFrames: calculateTotalDurationInFrames(props.scenes),
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Meta Ad Compositions */}
      <Composition
        id="meta-ad-1x1"
        component={MetaAd}
        width={1080}
        height={1080}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="meta-ad-9x16"
        component={MetaAd}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="meta-ad-16x9"
        component={MetaAd}
        width={1920}
        height={1080}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />

      {/* TikTok Ad Composition */}
      <Composition
        id="tiktok-ad"
        component={TikTokAd}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />

      {/* Generic Video Compositions */}
      <Composition
        id="generic-video-16x9"
        component={GenericVideo}
        width={1920}
        height={1080}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="generic-video-1x1"
        component={GenericVideo}
        width={1080}
        height={1080}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="generic-video-9x16"
        component={GenericVideo}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={calculateTotalDurationInFrames(defaultProps.scenes)}
        schema={videoInputPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
    </>
  );
};
