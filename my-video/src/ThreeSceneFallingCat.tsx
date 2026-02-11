import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

const SunMoon = ({ scene, width }: { scene: number; width: number }) => {
  const sunX = width / 2;
  const sunsetX = width - 150;
  const moonX = width - 100;

  if (scene === 1) {
    return (
      <g>
        <defs>
          <radialGradient id="sunGradient">
            <stop offset="0%" stopColor="#FFEAA7" />
            <stop offset="50%" stopColor="#FDCB6E" />
            <stop offset="100%" stopColor="#E17055" stopOpacity="0" />
          </radialGradient>
          <filter id="sunGlow">
            <feGaussianBlur stdDeviation="4" />
          </filter>
        </defs>
        <circle
          cx={sunX}
          cy={80}
          r={50}
          fill="url(#sunGradient)"
          filter="url(#sunGlow)"
          opacity={0.9}
        />
        <circle cx={sunX} cy={80} r={35} fill="#FFEAA7" />
      </g>
    );
  }

  if (scene === 2) {
    return (
      <g>
        <defs>
          <radialGradient id="sunsetGradient">
            <stop offset="0%" stopColor="#FF7675" />
            <stop offset="40%" stopColor="#E17055" />
            <stop offset="100%" stopColor="#D63031" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle
          cx={sunsetX}
          cy={150}
          r={60}
          fill="url(#sunsetGradient)"
          opacity={0.8}
        />
        <circle cx={sunsetX} cy={150} r={40} fill="#FF7675" />
      </g>
    );
  }

  return (
    <g>
      <defs>
        <radialGradient id="moonGradient">
          <stop offset="0%" stopColor="#DFE6E9" />
          <stop offset="100%" stopColor="#74B9FF" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle
        cx={moonX}
        cy={80}
        r={40}
        fill="url(#moonGradient)"
        opacity={0.8}
      />
      <circle cx={moonX} cy={80} r={30} fill="#DFE6E9" />
    </g>
  );
};

const CloudsWithTexture = ({ scene }: { scene: number }) => {
  if (scene === 1) {
    return (
      <g>
        <defs>
          <linearGradient id="cloudGrad1" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#DFE6E9" />
          </linearGradient>
          <filter id="cloudBlur">
            <feGaussianBlur stdDeviation="2" />
          </filter>
        </defs>
        <g filter="url(#cloudBlur)" opacity={0.8}>
          <ellipse cx={180} cy={100} rx={80} ry={40} fill="url(#cloudGrad1)" />
          <ellipse cx={280} cy={80} rx={60} ry={30} fill="url(#cloudGrad1)" />
          <ellipse cx={550} cy={120} rx={70} ry={35} fill="url(#cloudGrad1)" />
          <ellipse cx={700} cy={90} rx={55} ry={28} fill="url(#cloudGrad1)" />
        </g>
      </g>
    );
  }

  if (scene === 2) {
    return (
      <g>
        <defs>
          <linearGradient
            id="sunsetCloudGrad"
            x1="0%"
            y1="0%"
            x2="0%"
            y2="100%"
          >
            <stop offset="0%" stopColor="#FDCB6E" />
            <stop offset="100%" stopColor="#E17055" />
          </linearGradient>
        </defs>
        <g opacity={0.7}>
          <ellipse
            cx={150}
            cy={180}
            rx={60}
            ry={30}
            fill="url(#sunsetCloudGrad)"
          />
          <ellipse
            cx={350}
            cy={150}
            rx={50}
            ry={25}
            fill="url(#sunsetCloudGrad)"
          />
          <ellipse
            cx={600}
            cy={170}
            rx={65}
            ry={32}
            fill="url(#sunsetCloudGrad)"
          />
          <ellipse
            cx={850}
            cy={140}
            rx={45}
            ry={22}
            fill="url(#sunsetCloudGrad)"
          />
        </g>
      </g>
    );
  }

  return (
    <g>
      <defs>
        <linearGradient id="nightCloudGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#636E72" />
          <stop offset="100%" stopColor="#2D3436" />
        </linearGradient>
      </defs>
      <g opacity={0.4}>
        <ellipse cx={200} cy={60} rx={55} ry={28} fill="url(#nightCloudGrad)" />
        <ellipse cx={450} cy={50} rx={45} ry={22} fill="url(#nightCloudGrad)" />
        <ellipse cx={700} cy={65} rx={50} ry={25} fill="url(#nightCloudGrad)" />
      </g>
    </g>
  );
};

const CityWithTexture = ({
  height,
  scene,
}: {
  height: number;
  scene: number;
}) => {
  const buildings = [
    { x: 30, w: 70, h: 220, color: "#2C3E50" },
    { x: 120, w: 90, h: 300, color: "#34495E" },
    { x: 230, w: 60, h: 200, color: "#2C3E50" },
    { x: 310, w: 110, h: 350, color: "#1A252F" },
    { x: 440, w: 80, h: 250, color: "#34495E" },
    { x: 540, w: 100, h: 280, color: "#2C3E50" },
    { x: 660, w: 70, h: 230, color: "#34495E" },
    { x: 750, w: 90, h: 320, color: "#1A252F" },
    { x: 860, w: 80, h: 260, color: "#34495E" },
    { x: 960, w: 100, h: 300, color: "#2C3E50" },
    { x: 1080, w: 70, h: 200, color: "#34495E" },
    { x: 1170, w: 110, h: 350, color: "#1A252F" },
  ];

  const buildingOpacity = scene === 1 ? 0.9 : scene === 2 ? 0.6 : 0.3;
  const blurAmount = scene === 2 ? 2 : 0;

  return (
    <g>
      <defs>
        <linearGradient id="buildingGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1A1A2E" />
          <stop offset="50%" stopColor="#2D3436" />
          <stop offset="100%" stopColor="#1A1A2E" />
        </linearGradient>
      </defs>

      {buildings.map((b, i) => (
        <g key={i} filter={`blur(${blurAmount}px)`} opacity={buildingOpacity}>
          <rect
            x={b.x}
            y={height - 300 - b.h * 0.6}
            width={b.w}
            height={b.h * 0.6}
            fill={scene === 1 ? b.color : "url(#buildingGrad)"}
          />
          {Array.from({ length: Math.floor((b.h * 0.6) / 35) }).map(
            (_, floor) => (
              <rect
                key={floor}
                x={b.x + 8}
                y={height - 290 - b.h * 0.6 + floor * 32}
                width={b.w - 16}
                height={20}
                fill={
                  floor === 2 && i === 2
                    ? "#FFEAA7"
                    : scene === 1
                      ? "#4A5568"
                      : "#636E72"
                }
                opacity={0.8}
              />
            ),
          )}
        </g>
      ))}
    </g>
  );
};

const DetailedBuilding = ({
  width,
  height,
}: {
  width: number;
  height: number;
}) => {
  const buildingWidth = 160;
  const buildingHeight = height - 100;
  const buildingX = width / 2 - buildingWidth / 2 + 50;

  return (
    <g>
      <defs>
        <linearGradient id="buildingWall" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#2C3E50" />
          <stop offset="30%" stopColor="#34495E" />
          <stop offset="70%" stopColor="#34495E" />
          <stop offset="100%" stopColor="#2C3E50" />
        </linearGradient>
        <radialGradient id="windowGlow">
          <stop offset="0%" stopColor="#FFEAA7" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#FFEAA7" stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect
        x={buildingX}
        y={50}
        width={buildingWidth}
        height={buildingHeight}
        fill="url(#buildingWall)"
      />

      {Array.from({ length: 12 }).map((_, floor) =>
        Array.from({ length: 6 }).map((_, col) => {
          const isLit = floor === 3 && col === 2;
          return (
            <g key={`${floor}-${col}`}>
              <rect
                x={buildingX + 15 + col * 24}
                y={70 + floor * 28}
                width={18}
                height={22}
                fill="#1A252F"
                stroke="#0D1318"
                strokeWidth={0.5}
              />
              <rect
                x={buildingX + 17 + col * 24}
                y={72 + floor * 28}
                width={14}
                height={18}
                fill={isLit ? "#FFEAA7" : "#4A5568"}
                opacity={0.9}
              />
              {isLit && (
                <rect
                  x={buildingX + 17 + col * 24}
                  y={72 + floor * 28}
                  width={14}
                  height={18}
                  fill="url(#windowGlow)"
                  opacity={0.5}
                />
              )}
            </g>
          );
        }),
      )}

      <rect
        x={buildingX - 12}
        y={42}
        width={buildingWidth + 24}
        height={12}
        fill="#C0392B"
      />
      <rect
        x={buildingX - 8}
        y={38}
        width={buildingWidth + 16}
        height={5}
        fill="#A93226"
      />
      <rect
        x={buildingX + buildingWidth - 40}
        y={52}
        width={35}
        height={8}
        fill="#8B4513"
        stroke="#5D3A1A"
        strokeWidth={1}
      />
    </g>
  );
};

const GroundWithTexture = ({
  width,
  height,
  scene,
}: {
  width: number;
  height: number;
  scene: number;
}) => {
  const grassColor =
    scene === 1 ? "#27AE60" : scene === 2 ? "#E17055" : "#2D3436";

  return (
    <g>
      <rect x={0} y={height - 80} width={width} height={80} fill={grassColor} />
      <defs>
        <pattern
          id="grassPattern"
          width="20"
          height="10"
          patternUnits="userSpaceOnUse"
        >
          <line
            x1="0"
            y1="10"
            x2="10"
            y2="0"
            stroke="#2ECC71"
            strokeWidth="2"
          />
          <line
            x1="10"
            y1="10"
            x2="20"
            y2="0"
            stroke="#27AE60"
            strokeWidth="2"
          />
        </pattern>
      </defs>
      <rect
        x={0}
        y={height - 80}
        width={width}
        height={80}
        fill="url(#grassPattern)"
        opacity={0.3}
      />

      {scene === 3 && (
        <ellipse
          cx={width / 2 + 50}
          cy={height - 80}
          rx={50}
          ry={20}
          fill="rgba(139, 69, 19, 0.6)"
        />
      )}
    </g>
  );
};

const CatWithFurTexture = ({
  frame,
  fps,
  scene,
}: {
  frame: number;
  fps: number;
  scene: number;
}) => {
  const fallTime = (frame - 60) / fps;
  const landProgress = (frame - 120) / fps;

  const x = 640 + 50;
  let y = 55;
  let rotation = 0;

  if (scene === 2) {
    y = 80 + 0.5 * 9.8 * fallTime * fallTime * 20;
    rotation = interpolate(fallTime, [0, 2], [0, -Math.PI * 2.3]);
  } else if (scene === 3) {
    const bounce1 = spring({
      frame: landProgress * 60,
      fps,
      from: 30,
      to: 0,
      durationInFrames: 20,
    });
    const bounce2 = spring({
      frame: landProgress * 60 - 20,
      fps,
      from: 12,
      to: 0,
      durationInFrames: 15,
    });
    const bounce3 = spring({
      frame: landProgress * 60 - 35,
      fps,
      from: 5,
      to: 0,
      durationInFrames: 10,
    });
    const totalBounce = Math.max(0, bounce1 + bounce2 + bounce3);
    y = 620 - totalBounce;
  }

  const tailWag =
    scene === 1
      ? Math.sin((frame / fps) * 5) * 0.3
      : scene === 2
        ? Math.sin(fallTime * 12) * 0.5
        : Math.sin(landProgress * 20) * 0.2;

  return (
    <g
      transform={`translate(${x}, ${y}) rotate(${(rotation * 180) / Math.PI})`}
    >
      <defs>
        <linearGradient id="catFur" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#E67E22" />
          <stop offset="50%" stopColor="#D35400" />
          <stop offset="100%" stopColor="#A04000" />
        </linearGradient>
        <linearGradient id="catBelly" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#F5B041" />
          <stop offset="100%" stopColor="#E67E22" />
        </linearGradient>
      </defs>

      <ellipse
        cx={0}
        cy={0}
        rx={45}
        ry={28}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="2"
      />
      <ellipse
        cx={0}
        cy={12}
        rx={28}
        ry={14}
        fill="url(#catBelly)"
        stroke="#D35400"
        strokeWidth="1"
      />

      <circle
        cx={0}
        cy={-32}
        r={22}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="2"
      />
      <ellipse cx={-10} cy={-35} rx={5} ry={6} fill="#FFFFFF" />
      <ellipse cx={10} cy={-35} rx={5} ry={6} fill="#FFFFFF" />
      <circle cx={-10} cy={-35} r={2.5} fill="#1A1A2E" />
      <circle cx={10} cy={-35} r={2.5} fill="#1A1A2E" />
      <circle cx={-9} cy={-36} r={1} fill="#FFFFFF" opacity={0.8} />
      <circle cx={11} cy={-36} r={1} fill="#FFFFFF" opacity={0.8} />
      <path d="M -4,-29 Q 0,-27 4,-29 Q 0,-31 -4,-29" fill="#E74C3C" />

      <path
        d="M -18,-48 L -8,-36 L -22,-36 Z"
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />
      <path
        d="M 18,-48 L 8,-36 L 22,-36 Z"
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />

      <line
        x1={-24}
        y1={-30}
        x2={-8}
        y2={-30}
        stroke="#A04000"
        strokeWidth="0.8"
      />
      <line
        x1={-24}
        y1={-27}
        x2={-8}
        y2={-27}
        stroke="#A04000"
        strokeWidth="0.8"
      />
      <line
        x1={-24}
        y1={-33}
        x2={-8}
        y2={-33}
        stroke="#A04000"
        strokeWidth="0.8"
      />
      <line
        x1={24}
        y1={-30}
        x2={8}
        y2={-30}
        stroke="#A04000"
        strokeWidth="0.8"
      />
      <line
        x1={24}
        y1={-27}
        x2={8}
        y2={-27}
        stroke="#A04000"
        strokeWidth="0.8"
      />
      <line
        x1={24}
        y1={-33}
        x2={8}
        y2={-33}
        stroke="#A04000"
        strokeWidth="0.8"
      />

      <ellipse
        cx={-26}
        cy={18}
        rx={8}
        ry={15}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />
      <ellipse
        cx={26}
        cy={18}
        rx={8}
        ry={15}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />
      <ellipse
        cx={-40}
        cy={28}
        rx={10}
        ry={20}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />
      <ellipse
        cx={40}
        cy={28}
        rx={10}
        ry={20}
        fill="url(#catFur)"
        stroke="#A04000"
        strokeWidth="1"
      />

      <path
        d={`M 45,5 Q ${45 + 25 * Math.cos(tailWag)},${5 + 15 * Math.sin(tailWag)} Q ${45 + 15 * Math.cos(tailWag * 2)},${5 + 25 * Math.sin(tailWag * 2)} Q ${45 + 5 * Math.cos(tailWag * 3)},${5 + 35 * Math.sin(tailWag * 3)}`}
        stroke="url(#catFur)"
        strokeWidth="7"
        strokeLinecap="round"
        fill="none"
      />
    </g>
  );
};

const MotionBlurLayers = ({
  y,
  rotation,
  blurLayers,
}: {
  y: number;
  rotation: number;
  blurLayers: number;
}) => {
  return (
    <g>
      {Array.from({ length: blurLayers }).map((_, i) => (
        <g
          key={i}
          transform={`translate(690, ${y + (i + 1) * 8}) rotate(${(rotation * 180) / Math.PI + i * 8})`}
          opacity={0.12 * (blurLayers - i)}
          filter="url(#motionBlur)"
        >
          <ellipse cx={0} cy={0} rx={45} ry={28} fill="#E67E22" />
          <circle cx={0} cy={-32} r={22} fill="#D35400" />
        </g>
      ))}
    </g>
  );
};

export const ThreeSceneFallingCat = () => {
  const frame = useCurrentFrame();
  const { width, fps } = useVideoConfig();

  let scene = 1;
  let bgGradient = "";

  if (frame < 60) {
    scene = 1;
    bgGradient =
      "linear-gradient(to bottom, #74B9FF 0%, #81ECEC 40%, #A29BFE 70%, #6C5CE7 100%)";
  } else if (frame < 120) {
    scene = 2;
    bgGradient =
      "linear-gradient(to bottom, #A29BFE 0%, #FD79A8 30%, #E17055 60%, #D63031 100%)";
  } else {
    scene = 3;
    bgGradient =
      "linear-gradient(to bottom, #0984E3 0%, #74B9FF 40%, #55EFC4 80%, #00B894 100%)";
  }

  const fallTime = scene === 2 ? (frame - 60) / fps : 0;
  const fallY = scene === 2 ? 80 + 0.5 * 9.8 * fallTime * fallTime * 20 : 80;
  const fallRotation = scene === 2 ? -Math.PI * 2.3 : 0;

  return (
    <svg width="100%" height="100%" style={{ background: bgGradient }}>
      <defs>
        <filter id="motionBlur">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>

      <SunMoon scene={scene} width={width} />
      <CloudsWithTexture scene={scene} />
      <CityWithTexture height={720} scene={scene} />
      <DetailedBuilding width={width} height={720} />
      <GroundWithTexture width={width} height={720} scene={scene} />

      {scene === 1 && <CatWithFurTexture frame={frame} fps={fps} scene={1} />}
      {scene === 2 && (
        <>
          <MotionBlurLayers y={fallY} rotation={fallRotation} blurLayers={5} />
          <CatWithFurTexture frame={frame} fps={fps} scene={2} />
        </>
      )}
      {scene === 3 && <CatWithFurTexture frame={frame} fps={fps} scene={3} />}

      <text
        x={20}
        y={35}
        fill="white"
        fontSize={16}
        fontWeight="bold"
        opacity={0.9}
      >
        {scene === 1
          ? "场景1: 清晨楼顶"
          : scene === 2
            ? "场景2: 黄昏下落"
            : "场景3: 傍晚落地"}
      </text>

      <text
        x={width - 20}
        y={35}
        textAnchor="end"
        fill="white"
        fontSize={14}
        opacity={0.8}
      >
        {(frame / fps).toFixed(1)}s
      </text>

      <text
        x={width / 2}
        y={55}
        textAnchor="middle"
        fill="white"
        fontSize={18}
        fontWeight="bold"
        opacity={0.85}
      >
        猫咪三阶段跳楼动画
      </text>
    </svg>
  );
};
