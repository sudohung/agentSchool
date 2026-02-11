import { useCurrentFrame, interpolate } from "remotion";

interface BranchProps {
  x: number;
  y: number;
  length: number;
  angle: number;
  depth: number;
  maxDepth: number;
  branchWidth: number;
  wind: number;
}

const Branch = ({
  x,
  y,
  length,
  angle,
  depth,
  maxDepth,
  branchWidth,
  wind,
}: BranchProps) => {
  if (depth > maxDepth) return null;

  const endX = x + length * Math.sin(angle);
  const endY = y - length * Math.cos(angle);

  const windEffect = wind * Math.sin(depth * 0.5) * (depth * 0.5);

  return (
    <>
      <line
        x1={x}
        y1={y}
        x2={endX}
        y2={endY}
        stroke={`hsl(${120 + depth * 10}, 70%, ${30 + depth * 5}%)`}
        strokeWidth={branchWidth}
        strokeLinecap="round"
      />
      <Branch
        x={endX}
        y={endY}
        length={length * 0.7}
        angle={angle + 0.4 + windEffect}
        depth={depth + 1}
        maxDepth={maxDepth}
        branchWidth={branchWidth * 0.7}
        wind={wind}
      />
      <Branch
        x={endX}
        y={endY}
        length={length * 0.7}
        angle={angle - 0.4 + windEffect}
        depth={depth + 1}
        maxDepth={maxDepth}
        branchWidth={branchWidth * 0.7}
        wind={wind}
      />
    </>
  );
};

interface FractalTreeProps {
  maxDepth?: number;
}

export const FractalTree = ({ maxDepth = 10 }: FractalTreeProps) => {
  const frame = useCurrentFrame();
  const fullTreeHeight = 180;

  const growthProgress = interpolate(frame, [0, 200], [0, 1], {
    extrapolateRight: "clamp",
  });

  const treeHeight = fullTreeHeight * growthProgress;
  const branchWidth = 12 * growthProgress;

  const animatedWind = interpolate(frame, [0, 300], [-0.05, 0.05], {
    extrapolateRight: "clamp",
  });

  if (growthProgress === 0) {
    return (
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYBottom"
      >
        <rect width="100%" height="100%" fill="#1a1a2e" />
        <ellipse cx="400" cy="600" rx="80" ry="20" fill="rgba(0,0,0,0.3)" />
      </svg>
    );
  }

  return (
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 800 600"
      preserveAspectRatio="xMidYBottom"
    >
      <defs>
        <linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#1a1a2e" />
          <stop offset="100%" stopColor="#16213e" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect width="100%" height="100%" fill="url(#skyGradient)" />
      <Branch
        x={400}
        y={600}
        length={treeHeight}
        angle={0}
        depth={0}
        maxDepth={maxDepth}
        branchWidth={branchWidth}
        wind={animatedWind}
      />
      <circle
        cx="400"
        cy={600 - treeHeight}
        r={8 * growthProgress}
        fill={`hsla(${120 + frame * 0.5}, 100%, 70%, ${0.8 * growthProgress})`}
        filter="url(#glow)"
      />
      <ellipse cx="400" cy="600" rx="80" ry="20" fill="rgba(0,0,0,0.3)" />
    </svg>
  );
};
