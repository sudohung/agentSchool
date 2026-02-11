import { useState } from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { FractalTree } from "./FractalTree";

export const RollingBall = () => {
  const { width } = useVideoConfig();
  const frame = useCurrentFrame();

  const translateX = spring({
    frame,
    fps: 30,
    from: -100,
    to: width - 100,
    durationInFrames: 120,
  });

  const rotation = interpolate(
    translateX,
    [-100, width - 100],
    [0, Math.PI * 4],
  );

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "#1a1a2e",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: "50%",
          backgroundColor: "#ff6b6b",
          transform: `translateX(${translateX}px) rotate(${rotation}rad)`,
          boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24,
          color: "white",
          fontWeight: "bold",
        }}
      >
        ⚽
      </div>
    </div>
  );
};

const AnimationSelector = () => {
  const [selected, setSelected] = useState<"ball" | "tree">("tree");

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <div
        style={{
          position: "absolute",
          top: 20,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 100,
          display: "flex",
          gap: 10,
          backgroundColor: "rgba(0,0,0,0.5)",
          padding: 10,
          borderRadius: 8,
        }}
      >
        <button
          onClick={() => setSelected("ball")}
          style={{
            padding: "8px 20px",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
            backgroundColor: selected === "ball" ? "#ff6b6b" : "#333",
            color: "white",
            fontSize: 14,
            fontWeight: "bold",
            transition: "all 0.3s",
          }}
        >
          滚动的球
        </button>
        <button
          onClick={() => setSelected("tree")}
          style={{
            padding: "8px 20px",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
            backgroundColor: selected === "tree" ? "#4ecdc4" : "#333",
            color: "white",
            fontSize: 14,
            fontWeight: "bold",
            transition: "all 0.3s",
          }}
        >
          分形树
        </button>
      </div>
      {selected === "ball" ? <RollingBall /> : <FractalTree maxDepth={10} />}
    </div>
  );
};

export const MyComposition = () => {
  return <AnimationSelector />;
};
