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
  status = "idle",
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
  status?: "idle" | "active" | "completed" | "waiting";
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 30,
  });

  if (progress <= 0) return null;

  const currentSize = size * progress;
  const currentOpacity = progress;

  // 根据状态设置颜色
  let fillColor = color;
  let strokeColor = "white";
  let strokeWidth = 2;
  
  if (status === "active") {
    strokeColor = "#ffd700";
    strokeWidth = 4;
  } else if (status === "completed") {
    strokeColor = "#00b894";
    strokeWidth = 3;
  } else if (status === "waiting") {
    strokeColor = "#666";
    strokeWidth = 2;
  }

  if (layer === "coordinator") {
    strokeColor = "#ffd700";
    strokeWidth = 4;
  }

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: currentOpacity }}>
      <circle r={currentSize / 2} fill={fillColor} stroke={strokeColor} strokeWidth={strokeWidth} />
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
      {layer === "coordinator" && status === "active" && (
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

const HumanReviewGate = ({
  x,
  y,
  frame,
  delay,
  isActive = false,
}: {
  x: number;
  y: number;
  frame: number;
  delay: number;
  isActive?: boolean;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 25,
  });

  if (progress <= 0) return null;

  const gateColor = isActive ? "#ffd700" : "#666";
  const glowEffect = isActive ? "url(#glow)" : "none";

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: progress }}>
      <circle r={25} fill={gateColor} stroke="white" strokeWidth={2} filter={glowEffect} />
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
        fill={gateColor}
        fontSize={10}
      >
        审核
      </text>
    </g>
  );
};

const WaveIndicator = ({
  x,
  y,
  waveNumber,
  frame,
  delay,
  isActive = false,
}: {
  x: number;
  y: number;
  waveNumber: number;
  frame: number;
  delay: number;
  isActive?: boolean;
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
      <rect x={-40} y={-12} width={80} height={24} rx={12} fill={bgColor} />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fill={textColor}
        fontSize={11}
        fontWeight="bold"
      >
        第{waveNumber}波
      </text>
    </g>
  );
};

export const AgentCollaborationFlowCorrected = () => {
  const frame = useCurrentFrame();

  // 总时长 900 帧，分三个主要阶段
  const totalDuration = 900;
  const analysisPhase = 300;   // 0-300
  const optimizationPhase = 300; // 300-600  
  const executionPhase = 300;   // 600-900

  // 当前阶段
  const currentPhase = Math.floor((frame % totalDuration) / 300);

  // 分析阶段内的波次
  const analysisFrame = frame % totalDuration;
  const wave1Active = analysisFrame >= 0 && analysisFrame < 100;
  const wave2Active = analysisFrame >= 100 && analysisFrame < 200;
  const review1Active = analysisFrame >= 200 && analysisFrame < 300;

  // 优化阶段
  const optimizationFrame = analysisFrame - 300;
  const optimizationActive = analysisFrame >= 300 && analysisFrame < 500;
  const review2Active = analysisFrame >= 500 && analysisFrame < 600;

  // 执行阶段
  const executionFrame = analysisFrame - 600;
  const executionActive = analysisFrame >= 600 && analysisFrame < 800;
  const review3Active = analysisFrame >= 800 && analysisFrame < 900;

  return (
    <svg
      width="100%"
      height="100%"
      viewBox="0 0 1200 800"
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
        Agent 协作框架 - 精确三阶段流程 (Exact 3-Phase Workflow)
      </text>

      {/* 阶段标题 */}
      <g transform="translate(0, 60)">
        <text x={200} y={0} textAnchor="middle" fill={currentPhase === 0 ? "#4ecdc4" : "#888"} fontSize={16} fontWeight="bold">
          阶段一：分析阶段
        </text>
        <text x={600} y={0} textAnchor="middle" fill={currentPhase === 1 ? "#ff7675" : "#888"} fontSize={16} fontWeight="bold">
          阶段二：优化阶段
        </text>
        <text x={1000} y={0} textAnchor="middle" fill={currentPhase === 2 ? "#00b894" : "#888"} fontSize={16} fontWeight="bold">
          阶段三：执行阶段
        </text>
      </g>

      {/* 协调者 - 始终显示 */}
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
        status="active"
      />

      {/* ===== 阶段一：分析阶段 ===== */}
      {currentPhase === 0 && (
        <g>
          {/* 第一波并行 */}
          <WaveIndicator x={300} y={250} waveNumber={1} frame={frame} delay={10} isActive={wave1Active} />
          <AgentNode
            x={300}
            y={300}
            label="项目扫描器"
            color="#74b9ff"
            icon="🔍"
            frame={frame}
            delay={wave1Active ? 30 : -1000}
            status={wave1Active ? "active" : "completed"}
          />
          <AgentNode
            x={500}
            y={300}
            label="架构分析器"
            color="#00cec9"
            icon="🏗️"
            frame={frame}
            delay={wave1Active ? 50 : -1000}
            status={wave1Active ? "active" : "completed"}
          />

          {/* 第二波并行 */}
          <WaveIndicator x={900} y={250} waveNumber={2} frame={frame} delay={wave2Active ? 110 : -1000} isActive={wave2Active} />
          <AgentNode
            x={700}
            y={300}
            label="业务分析器"
            color="#fdcb6e"
            icon="📊"
            frame={frame}
            delay={wave2Active ? 130 : -1000}
            status={wave2Active ? "active" : "completed"}
          />
          <AgentNode
            x={900}
            y={300}
            label="问题识别器"
            color="#e17055"
            icon="⚠️"
            frame={frame}
            delay={wave2Active ? 150 : -1000}
            status={wave2Active ? "active" : "completed"}
          />

          {/* 连接线 */}
          <Arrow
            startX={600}
            startY={120}
            endX={300}
            endY={300}
            frame={frame}
            delay={wave1Active ? 20 : -1000}
          />
          <Arrow
            startX={600}
            startY={120}
            endX={500}
            endY={300}
            frame={frame}
            delay={wave1Active ? 40 : -1000}
          />
          <Arrow
            startX={600}
            startY={120}
            endX={700}
            endY={300}
            frame={frame}
            delay={wave2Active ? 120 : -1000}
          />
          <Arrow
            startX={600}
            startY={120}
            endX={900}
            endY={300}
            frame={frame}
            delay={wave2Active ? 140 : -1000}
          />

          {/* 人工审核门禁1 */}
          <HumanReviewGate
            x={600}
            y={400}
            frame={frame}
            delay={review1Active ? 210 : -1000}
            isActive={review1Active}
          />
          <Arrow
            startX={600}
            startY={300}
            endX={600}
            endY={400}
            frame={frame}
            delay={review1Active ? 200 : -1000}
          />
        </g>
      )}

      {/* ===== 阶段二：优化阶段 ===== */}
      {currentPhase === 1 && (
        <g>
          <AgentNode
            x={400}
            y={300}
            label="重构专家"
            color="#ff7675"
            icon="🔄"
            frame={frame}
            delay={optimizationActive ? 320 : -1000}
            layer="execution"
            status={optimizationActive ? "active" : "completed"}
          />
          <AgentNode
            x={800}
            y={300}
            label="性能优化专家"
            color="#fd79a8"
            icon="⚡"
            frame={frame}
            delay={optimizationActive ? 340 : -1000}
            layer="execution"
            status={optimizationActive ? "active" : "completed"}
          />

          <Arrow
            startX={600}
            startY={120}
            endX={400}
            endY={300}
            frame={frame}
            delay={optimizationActive ? 310 : -1000}
            color="#ff7675"
          />
          <Arrow
            startX={600}
            startY={120}
            endX={800}
            endY={300}
            frame={frame}
            delay={optimizationActive ? 330 : -1000}
            color="#fd79a8"
          />

          {/* 人工审核门禁2 */}
          <HumanReviewGate
            x={600}
            y={400}
            frame={frame}
            delay={review2Active ? 510 : -1000}
            isActive={review2Active}
          />
          <Arrow
            startX={600}
            startY={300}
            endX={600}
            endY={400}
            frame={frame}
            delay={review2Active ? 500 : -1000}
          />
        </g>
      )}

      {/* ===== 阶段三：执行阶段 ===== */}
      {currentPhase === 2 && (
        <g>
          <AgentNode
            x={400}
            y={300}
            label="重构执行"
            color="#ff7675"
            icon="🛠️"
            frame={frame}
            delay={executionActive ? 620 : -1000}
            layer="execution"
            status={executionActive ? "active" : "completed"}
          />
          <AgentNode
            x={800}
            y={300}
            label="性能执行"
            color="#fd79a8"
            icon="🚀"
            frame={frame}
            delay={executionActive ? 640 : -1000}
            layer="execution"
            status={executionActive ? "active" : "completed"}
          />
          <AgentNode
            x={600}
            y={450}
            label="测试代理"
            color="#00b894"
            icon="🧪"
            frame={frame}
            delay={executionActive ? 660 : -1000}
            layer="verification"
            status={executionActive ? "active" : "completed"}
          />

          <Arrow
            startX={600}
            startY={120}
            endX={400}
            endY={300}
            frame={frame}
            delay={executionActive ? 610 : -1000}
            color="#ff7675"
          />
          <Arrow
            startX={600}
            startY={120}
            endX={800}
            endY={300}
            frame={frame}
            delay={executionActive ? 630 : -1000}
            color="#fd79a8"
          />
          <Arrow
            startX={600}
            startY={120}
            endX={600}
            endY={450}
            frame={frame}
            delay={executionActive ? 650 : -1000}
            color="#00b894"
          />

          {/* 执行到测试的连接 */}
          <Arrow
            startX={400}
            startY={300}
            endX={600}
            endY={450}
            frame={frame}
            delay={executionActive ? 670 : -1000}
            color="#aaa"
            dashed={true}
          />
          <Arrow
            startX={800}
            startY={300}
            endX={600}
            endY={450}
            frame={frame}
            delay={executionActive ? 680 : -1000}
            color="#aaa"
            dashed={true}
          />

          {/* 人工验收门禁3 */}
          <HumanReviewGate
            x={600}
            y={550}
            frame={frame}
            delay={review3Active ? 810 : -1000}
            isActive={review3Active}
          />
          <Arrow
            startX={600}
            startY={450}
            endX={600}
            endY={550}
            frame={frame}
            delay={review3Active ? 800 : -1000}
          />
        </g>
      )}

      {/* 状态显示 */}
      <g transform="translate(50, 750)">
        <text fill="#888" fontSize={12}>
          当前帧: {frame} | 阶段: {["分析", "优化", "执行"][currentPhase]}
        </text>
      </g>

      {/* 图例 */}
      <g transform="translate(950, 650)">
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