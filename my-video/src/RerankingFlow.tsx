import { useCurrentFrame, interpolate, spring } from "remotion";

const FlowNode = ({
  x,
  y,
  label,
  color,
  icon,
  frame,
  delay,
  size = 80,
}: {
  x: number;
  y: number;
  label: string;
  color: string;
  icon: string;
  frame: number;
  delay: number;
  size?: number;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 30,
  });

  const currentSize = size * progress;
  const currentOpacity = progress;

  if (progress <= 0) return null;

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: currentOpacity }}>
      <circle r={currentSize / 2} fill={color} stroke="white" strokeWidth={3} />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        dy={-5}
        fill="white"
        fontSize={24}
      >
        {icon}
      </text>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        dy={15}
        fill="white"
        fontSize={11}
        fontWeight="bold"
      >
        {label}
      </text>
    </g>
  );
};

const Arrow = ({
  startX,
  startY,
  endX,
  endY,
  frame,
  delay,
  color = "#4ecdc4",
}: {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  frame: number;
  delay: number;
  color?: string;
}) => {
  const progress = interpolate(frame - delay, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  if (progress <= 0) return null;

  const currentEndX = startX + (endX - startX) * progress;
  const currentEndY = startY + (endY - startY) * progress;

  return (
    <g>
      <line
        x1={startX}
        y1={startY}
        x2={currentEndX}
        y2={currentEndY}
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
      />
      {progress > 0.5 && (
        <polygon
          points={`${currentEndX},${currentEndY} ${currentEndX - 10},${currentEndY - 5} ${currentEndX - 10},${currentEndY + 5}`}
          fill={color}
        />
      )}
    </g>
  );
};

const DocumentIcon = ({
  x,
  y,
  frame,
  delay,
  rank,
}: {
  x: number;
  y: number;
  frame: number;
  delay: number;
  rank: number;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 40,
  });

  if (progress <= 0) return null;

  const offsetY = (rank - 1) * 35;

  return (
    <g
      transform={`translate(${x}, ${y + offsetY * progress})`}
      style={{ opacity: progress }}
    >
      <rect
        x={-25}
        y={-15}
        width={50}
        height={30}
        fill="#2d3748"
        stroke="#4ecdc4"
        strokeWidth={1}
        rx={3}
      />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        y={0}
        fill="#4ecdc4"
        fontSize={12}
        fontWeight="bold"
      >
        Doc{rank}
      </text>
      {progress > 0.5 && (
        <text
          textAnchor="middle"
          dominantBaseline="middle"
          y={22}
          fill="#888"
          fontSize={9}
        >
          Score: {(0.9 - rank * 0.1).toFixed(2)}
        </text>
      )}
    </g>
  );
};

export const RerankingFlow = () => {
  const frame = useCurrentFrame();

  return (
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 900 600"
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
      }}
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation={3} result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <text
        x={450}
        y={35}
        textAnchor="middle"
        fill="white"
        fontSize={20}
        fontWeight="bold"
      >
        检索与重排流程 (Retrieval & Reranking Pipeline)
      </text>

      <g transform="translate(0, 60)">
        <FlowNode
          x={150}
          y={80}
          label="用户查询"
          color="#ff6b6b"
          icon="🔍"
          frame={frame}
          delay={0}
        />

        <Arrow
          startX={180}
          startY={80}
          endX={260}
          endY={80}
          frame={frame}
          delay={20}
        />

        <FlowNode
          x={320}
          y={80}
          label="向量检索"
          color="#4ecdc4"
          icon="📦"
          frame={frame}
          delay={40}
        />

        <Arrow
          startX={350}
          startY={80}
          endX={430}
          endY={80}
          frame={frame}
          delay={60}
        />

        <FlowNode
          x={490}
          y={80}
          label="召回候选"
          color="#ffd93d"
          icon="📋"
          frame={frame}
          delay={80}
          size={90}
        />

        <text x={490} y={135} textAnchor="middle" fill="#888" fontSize={10}>
          (1000+ 文档)
        </text>

        <Arrow
          startX={520}
          startY={80}
          endX={600}
          endY={80}
          frame={frame}
          delay={100}
        />

        <FlowNode
          x={660}
          y={80}
          label="粗排"
          color="#a29bfe"
          icon="⚡"
          frame={frame}
          delay={120}
        />

        <Arrow
          startX={690}
          startY={80}
          endX={770}
          endY={80}
          frame={frame}
          delay={140}
        />

        <FlowNode
          x={830}
          y={80}
          label="精排/重排"
          color="#fd79a8"
          icon="🎯"
          frame={frame}
          delay={160}
          size={95}
        />
      </g>

      <g transform="translate(0, 220)">
        <text
          x={450}
          y={0}
          textAnchor="middle"
          fill="white"
          fontSize={16}
          fontWeight="bold"
        >
          重排阶段详情 (Reranking Stages)
        </text>

        <FlowNode
          x={120}
          y={50}
          label="Pointwise"
          color="#74b9ff"
          icon="1️⃣"
          frame={frame}
          delay={200}
          size={75}
        />

        <Arrow
          startX={155}
          startY={50}
          endX={210}
          endY={50}
          frame={frame}
          delay={220}
        />

        <FlowNode
          x={270}
          y={50}
          label="语义重排"
          color="#a29bfe"
          icon="2️⃣"
          frame={frame}
          delay={240}
          size={75}
        />

        <Arrow
          startX={305}
          startY={50}
          endX={360}
          endY={50}
          frame={frame}
          delay={260}
        />

        <FlowNode
          x={420}
          y={50}
          label="特征重排"
          color="#fd79a8"
          icon="3️⃣"
          frame={frame}
          delay={280}
          size={75}
        />

        <Arrow
          startX={455}
          startY={50}
          endX={510}
          endY={50}
          frame={frame}
          delay={300}
        />

        <FlowNode
          x={570}
          y={50}
          label="集成融合"
          color="#00b894"
          icon="🔄"
          frame={frame}
          delay={320}
          size={75}
        />

        <Arrow
          startX={605}
          startY={50}
          endX={660}
          endY={50}
          frame={frame}
          delay={340}
        />

        <FlowNode
          x={720}
          y={50}
          label="在线学习"
          color="#fdcb6e"
          icon="📈"
          frame={frame}
          delay={360}
          size={75}
        />
      </g>

      <g transform="translate(200, 420)">
        <text
          x={250}
          y={-50}
          textAnchor="middle"
          fill="white"
          fontSize={14}
          fontWeight="bold"
        >
          最终排序结果 (Top-K Results)
        </text>

        <DocumentIcon x={0} y={0} frame={frame} delay={400} rank={1} />
        <DocumentIcon x={120} y={0} frame={frame} delay={420} rank={2} />
        <DocumentIcon x={240} y={0} frame={frame} delay={440} rank={3} />
        <DocumentIcon x={360} y={0} frame={frame} delay={460} rank={4} />
        <DocumentIcon x={480} y={0} frame={frame} delay={480} rank={5} />
      </g>

      <g transform="translate(100, 530)">
        <text x={700} y={0} textAnchor="middle" fill="#666" fontSize={11}>
          Frame: {frame} | 流程循环演示
        </text>
      </g>

      <circle cx={50} cy={550} r={8} fill="#4ecdc4" filter="url(#glow)" />
      <text x={70} y={555} fill="#888" fontSize={10}>
        活跃节点
      </text>

      <circle cx={180} cy={550} r={8} fill="#888" />
      <text x={200} y={555} fill="#888" fontSize={10}>
        待激活
      </text>
    </svg>
  );
};
