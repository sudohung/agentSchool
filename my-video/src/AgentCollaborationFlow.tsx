import { useCurrentFrame, interpolate, spring } from "remotion";

const AgentNode = ({
  x,
  y,
  label,
  color,
  icon,
  frame,
  delay,
  size = 80,
  layer = "analysis",
}: {
  x: number;
  y: number;
  label: string;
  color: string;
  icon: string;
  frame: number;
  delay: number;
  size?: number;
  layer?: string;
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

  // 根据层级设置不同的边框效果
  let strokeColor = "white";
  let strokeWidth = 3;
  if (layer === "coordinator") {
    strokeColor = "#ffd700";
    strokeWidth = 4;
  } else if (layer === "execution") {
    strokeColor = "#ff6b6b";
  } else if (layer === "verification") {
    strokeColor = "#00b894";
  }

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: currentOpacity }}>
      <circle r={currentSize / 2} fill={color} stroke={strokeColor} strokeWidth={strokeWidth} />
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
      {layer === "coordinator" && (
        <circle r={currentSize / 2 + 5} fill="none" stroke="#ffd700" strokeWidth={2} strokeDasharray="5,5" />
      )}
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
  dashed = false,
}: {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  frame: number;
  delay: number;
  color?: string;
  dashed?: boolean;
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
        strokeDasharray={dashed ? "5,5" : "none"}
      />
      {progress > 0.5 && !dashed && (
        <polygon
          points={`${currentEndX},${currentEndY} ${currentEndX - 10},${currentEndY - 5} ${currentEndX - 10},${currentEndY + 5}`}
          fill={color}
        />
      )}
    </g>
  );
};

const PhaseIndicator = ({
  x,
  y,
  label,
  isActive,
  frame,
  delay,
}: {
  x: number;
  y: number;
  label: string;
  isActive: boolean;
  frame: number;
  delay: number;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 20,
  });

  if (progress <= 0) return null;

  const bgColor = isActive ? "#4ecdc4" : "#2d3748";
  const textColor = isActive ? "white" : "#888";

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: progress }}>
      <rect x={-60} y={-15} width={120} height={30} rx={15} fill={bgColor} />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fill={textColor}
        fontSize={12}
        fontWeight="bold"
      >
        {label}
      </text>
    </g>
  );
};

const HumanReviewGate = ({
  x,
  y,
  frame,
  delay,
}: {
  x: number;
  y: number;
  frame: number;
  delay: number;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 25,
  });

  if (progress <= 0) return null;

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: progress }}>
      <circle r={25} fill="#ffd700" stroke="white" strokeWidth={2} />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fill="black"
        fontSize={16}
        fontWeight="bold"
      >
        👨‍💼
      </text>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        dy={35}
        fill="#ffd700"
        fontSize={10}
      >
        审核
      </text>
    </g>
  );
};

export const AgentCollaborationFlow = () => {
  const frame = useCurrentFrame();

  // 计算当前阶段
  const totalDuration = 600; // 总帧数
  const phaseDuration = totalDuration / 3;
  const currentPhase = Math.floor((frame % totalDuration) / phaseDuration);

  return (
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 1200 700"
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
        x={600}
        y={35}
        textAnchor="middle"
        fill="white"
        fontSize={24}
        fontWeight="bold"
      >
        Agent 协作框架 - 7+1 模型 (Agent Collaboration Framework)
      </text>

      {/* 阶段指示器 */}
      <g transform="translate(0, 60)">
        <PhaseIndicator
          x={300}
          y={0}
          label="分析阶段"
          isActive={currentPhase === 0}
          frame={frame}
          delay={0}
        />
        <PhaseIndicator
          x={600}
          y={0}
          label="优化阶段"
          isActive={currentPhase === 1}
          frame={frame}
          delay={20}
        />
        <PhaseIndicator
          x={900}
          y={0}
          label="执行阶段"
          isActive={currentPhase === 2}
          frame={frame}
          delay={40}
        />
      </g>

      {/* 协调者 */}
      <AgentNode
        x={600}
        y={120}
        label="协调者"
        color="#6c5ce7"
        icon="🧠"
        frame={frame}
        delay={0}
        size={100}
        layer="coordinator"
      />

      {/* 分析组 */}
      <g transform="translate(0, 250)">
        <AgentNode
          x={200}
          y={0}
          label="项目扫描器"
          color="#74b9ff"
          icon="🔍"
          frame={frame}
          delay={currentPhase === 0 ? 60 : -1000}
          layer="analysis"
        />
        <AgentNode
          x={400}
          y={0}
          label="架构分析器"
          color="#00cec9"
          icon="🏗️"
          frame={frame}
          delay={currentPhase === 0 ? 80 : -1000}
          layer="analysis"
        />
        <AgentNode
          x={800}
          y={0}
          label="业务分析器"
          color="#fdcb6e"
          icon="📊"
          frame={frame}
          delay={currentPhase === 0 ? 120 : -1000}
          layer="analysis"
        />
        <AgentNode
          x={1000}
          y={0}
          label="问题识别器"
          color="#e17055"
          icon="⚠️"
          frame={frame}
          delay={currentPhase === 0 ? 140 : -1000}
          layer="analysis"
        />
      </g>

      {/* 优化执行组 */}
      <g transform="translate(0, 400)">
        <AgentNode
          x={400}
          y={0}
          label="重构专家"
          color="#ff7675"
          icon="🔄"
          frame={frame}
          delay={currentPhase === 1 ? 200 : -1000}
          layer="execution"
        />
        <AgentNode
          x={800}
          y={0}
          label="性能优化专家"
          color="#fd79a8"
          icon="⚡"
          frame={frame}
          delay={currentPhase === 1 ? 220 : -1000}
          layer="execution"
        />
      </g>

      {/* 验证组 */}
      <AgentNode
        x={600}
        y={550}
        label="测试代理"
        color="#00b894"
        icon="🧪"
        frame={frame}
        delay={currentPhase === 2 ? 280 : -1000}
        layer="verification"
      />

      {/* 连接线 - 协调者到各层 */}
      <Arrow
        startX={600}
        startY={120}
        endX={200}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 50 : -1000}
        color="#74b9ff"
      />
      <Arrow
        startX={600}
        startY={120}
        endX={400}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 70 : -1000}
        color="#00cec9"
      />
      <Arrow
        startX={600}
        startY={120}
        endX={800}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 110 : -1000}
        color="#fdcb6e"
      />
      <Arrow
        startX={600}
        startY={120}
        endX={1000}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 130 : -1000}
        color="#e17055"
      />

      <Arrow
        startX={600}
        startY={120}
        endX={400}
        endY={400}
        frame={frame}
        delay={currentPhase === 1 ? 190 : -1000}
        color="#ff7675"
      />
      <Arrow
        startX={600}
        startY={120}
        endX={800}
        endY={400}
        frame={frame}
        delay={currentPhase === 1 ? 210 : -1000}
        color="#fd79a8"
      />

      <Arrow
        startX={600}
        startY={120}
        endX={600}
        endY={550}
        frame={frame}
        delay={currentPhase === 2 ? 270 : -1000}
        color="#00b894"
      />

      {/* 并行连接线 */}
      <Arrow
        startX={200}
        startY={250}
        endX={800}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 100 : -1000}
        color="#aaa"
        dashed={true}
      />
      <Arrow
        startX={400}
        startY={250}
        endX={1000}
        endY={250}
        frame={frame}
        delay={currentPhase === 0 ? 100 : -1000}
        color="#aaa"
        dashed={true}
      />

      {/* 人工审核门禁 */}
      <HumanReviewGate
        x={600}
        y={325}
        frame={frame}
        delay={currentPhase === 0 ? 180 : -1000}
      />
      <HumanReviewGate
        x={600}
        y={475}
        frame={frame}
        delay={currentPhase === 1 ? 260 : -1000}
      />

      {/* 状态显示 */}
      <g transform="translate(50, 650)">
        <text fill="#888" fontSize={12}>
          当前帧: {frame} | 阶段: {["分析", "优化", "执行"][currentPhase]}
        </text>
      </g>

      {/* 图例 */}
      <g transform="translate(950, 620)">
        <circle cx={0} cy={0} r={8} fill="#6c5ce7" stroke="#ffd700" strokeWidth={2} />
        <text x={15} y={5} fill="#888" fontSize={10}>协调者</text>
        
        <circle cx={0} cy={25} r={8} fill="#74b9ff" stroke="white" strokeWidth={2} />
        <text x={15} y={30} fill="#888" fontSize={10}>分析组</text>
        
        <circle cx={0} cy={50} r={8} fill="#ff7675" stroke="white" strokeWidth={2} />
        <text x={15} y={55} fill="#888" fontSize={10}>执行组</text>
        
        <circle cx={0} cy={75} r={8} fill="#00b894" stroke="white" strokeWidth={2} />
        <text x={15} y={80} fill="#888" fontSize={10}>验证组</text>
        
        <circle cx={0} cy={100} r={8} fill="#ffd700" stroke="white" strokeWidth={2} />
        <text x={15} y={105} fill="#888" fontSize={10}>人工审核</text>
      </g>
    </svg>
  );
};