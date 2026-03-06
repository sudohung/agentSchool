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

const PhaseTitle = ({
  x,
  y,
  text,
  frame,
  delay,
  isActive = false,
}: {
  x: number;
  y: number;
  text: string;
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

  const color = isActive ? "#4ecdc4" : "#888";

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: progress }}>
      <text textAnchor="middle" fill={color} fontSize={16} fontWeight="bold">
        {text}
      </text>
    </g>
  );
};

const ExecutionTask = ({
  x,
  y,
  label,
  type,
  frame,
  delay,
}: {
  x: number;
  y: number;
  label: string;
  type: "refactor" | "performance";
  frame: number;
  delay: number;
}) => {
  const progress = spring({
    frame: frame - delay,
    fps: 30,
    from: 0,
    to: 1,
    durationInFrames: 40,
  });

  if (progress <= 0) return null;

  const color = type === "refactor" ? "#ff7675" : "#fd79a8";
  const icon = type === "refactor" ? "🔄" : "⚡";

  return (
    <g transform={`translate(${x}, ${y})`} style={{ opacity: progress }}>
      <rect x={-40} y={-15} width={80} height={30} rx={8} fill={color} stroke="white" strokeWidth={2} />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        dy={-5}
        fill="white"
        fontSize={20}
      >
        {icon}
      </text>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        dy={12}
        fill="white"
        fontSize={10}
        fontWeight="bold"
      >
        {label}
      </text>
    </g>
  );
};

export const AgentCollaborationFlowExact = () => {
  const frame = useCurrentFrame();

  // 总时长 1200 帧，精确匹配所有步骤
  const totalDuration = 1200;

  // 分析阶段 (0-400)
  const analysisPhase = frame % totalDuration < 400;
  const analysisFrame = frame % totalDuration;

  // 第一波并行 (0-100)
  const wave1Active = analysisFrame >= 0 && analysisFrame < 100;
  const wave1Completed = analysisFrame >= 100;

  // 合并结果 (100-120)
  const mergingActive = analysisFrame >= 100 && analysisFrame < 120;

  // 第二波并行 (120-220)
  const wave2Active = analysisFrame >= 120 && analysisFrame < 220;
  const wave2Completed = analysisFrame >= 220;

  // 整合结果 (220-240)
  const integratingActive = analysisFrame >= 220 && analysisFrame < 240;

  // 人工审核1 (240-400)
  const review1Active = analysisFrame >= 240 && analysisFrame < 400;

  // 优化阶段 (400-700)
  const optimizationPhase = frame % totalDuration >= 400 && frame % totalDuration < 700;
  const optimizationFrame = frame % totalDuration - 400;

  // 并行制定方案 (0-150)
  const planningActive = optimizationFrame >= 0 && optimizationFrame < 150;
  const planningCompleted = optimizationFrame >= 150;

  // 冲突检测整合 (150-180)
  const conflictActive = optimizationFrame >= 150 && optimizationFrame < 180;

  // 人工审核2 (180-300)
  const review2Active = optimizationFrame >= 180 && optimizationFrame < 300;

  // 执行阶段 (700-1200)
  const executionPhase = frame % totalDuration >= 700;
  const executionFrame = frame % totalDuration - 700;

  // 执行重构任务 (0-80)
  const refactorExecuteActive = executionFrame >= 0 && executionFrame < 80;
  const refactorExecuteCompleted = executionFrame >= 80;

  // 测试验证重构 (80-120)
  const refactorTestActive = executionFrame >= 80 && executionFrame < 120;
  const refactorTestCompleted = executionFrame >= 120;

  // 执行性能任务 (120-200)
  const perfExecuteActive = executionFrame >= 120 && executionFrame < 200;
  const perfExecuteCompleted = executionFrame >= 200;

  // 测试验证性能 (200-240)
  const perfTestActive = executionFrame >= 200 && executionFrame < 240;
  const perfTestCompleted = executionFrame >= 240;

  // 生成报告 (240-260)
  const reportActive = executionFrame >= 240 && executionFrame < 260;

  // 人工验收3 (260-500)
  const review3Active = executionFrame >= 260 && executionFrame < 500;

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
        Agent 协作框架 - 精确时序流程 (Exact Timing Workflow)
      </text>

      {/* 阶段标题 */}
      <PhaseTitle x={200} y={60} text="阶段一：分析阶段" frame={frame} delay={0} isActive={analysisPhase} />
      <PhaseTitle x={600} y={60} text="阶段二：优化阶段" frame={frame} delay={400} isActive={optimizationPhase} />
      <PhaseTitle x={1000} y={60} text="阶段三：执行阶段" frame={frame} delay={700} isActive={executionPhase} />

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
      {analysisPhase && (
        <g>
          {/* 第一波并行 */}
          <AgentNode
            x={300}
            y={300}
            label="项目扫描器"
            color="#74b9ff"
            icon="🔍"
            frame={frame}
            delay={wave1Active ? 10 : -1000}
            status={wave1Active ? "active" : wave1Completed ? "completed" : "idle"}
          />
          <AgentNode
            x={500}
            y={300}
            label="架构分析器"
            color="#00cec9"
            icon="🏗️"
            frame={frame}
            delay={wave1Active ? 30 : -1000}
            status={wave1Active ? "active" : wave1Completed ? "completed" : "idle"}
          />

          {/* 连接线 - 第一波 */}
          <Arrow
            startX={600}
            startY={120}
            endX={300}
            endY={300}
            frame={frame}
            delay={wave1Active ? 0 : -1000}
          />
          <Arrow
            startX={600}
            startY={120}
            endX={500}
            endY={300}
            frame={frame}
            delay={wave1Active ? 20 : -1000}
          />

          {/* 合并结果指示 */}
          {mergingActive && (
            <text x={400} y={250} textAnchor="middle" fill="#4ecdc4" fontSize={14} fontWeight="bold">
              合并第一波结果...
            </text>
          )}

          {/* 第二波并行 */}
          <AgentNode
            x={700}
            y={300}
            label="业务分析器"
            color="#fdcb6e"
            icon="📊"
            frame={frame}
            delay={wave2Active ? 130 : -1000}
            status={wave2Active ? "active" : wave2Completed ? "completed" : "waiting"}
          />
          <AgentNode
            x={900}
            y={300}
            label="问题识别器"
            color="#e17055"
            icon="⚠️"
            frame={frame}
            delay={wave2Active ? 150 : -1000}
            status={wave2Active ? "active" : wave2Completed ? "completed" : "waiting"}
          />

          {/* 连接线 - 第二波 */}
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

          {/* 整合结果指示 */}
          {integratingActive && (
            <text x={800} y={250} textAnchor="middle" fill="#4ecdc4" fontSize={14} fontWeight="bold">
              整合分析结果...
            </text>
          )}

          {/* 人工审核门禁1 */}
          <HumanReviewGate
            x={600}
            y={400}
            frame={frame}
            delay={review1Active ? 250 : -1000}
            isActive={review1Active}
          />
          <Arrow
            startX={600}
            startY={300}
            endX={600}
            endY={400}
            frame={frame}
            delay={review1Active ? 240 : -1000}
          />
        </g>
      )}

      {/* ===== 阶段二：优化阶段 ===== */}
      {optimizationPhase && (
        <g>
          <AgentNode
            x={400}
            y={300}
            label="重构专家"
            color="#ff7675"
            icon="🔄"
            frame={frame}
            delay={planningActive ? 420 : -1000}
            layer="execution"
            status={planningActive ? "active" : planningCompleted ? "completed" : "idle"}
          />
          <AgentNode
            x={800}
            y={300}
            label="性能优化专家"
            color="#fd79a8"
            icon="⚡"
            frame={frame}
            delay={planningActive ? 440 : -1000}
            layer="execution"
            status={planningActive ? "active" : planningCompleted ? "completed" : "idle"}
          />

          <Arrow
            startX={600}
            startY={120}
            endX={400}
            endY={300}
            frame={frame}
            delay={planningActive ? 410 : -1000}
            color="#ff7675"
          />
          <Arrow
            startX={600}
            startY={120}
            endX={800}
            endY={300}
            frame={frame}
            delay={planningActive ? 430 : -1000}
            color="#fd79a8"
          />

          {/* 冲突检测指示 */}
          {conflictActive && (
            <text x={600} y={250} textAnchor="middle" fill="#ff7675" fontSize={14} fontWeight="bold">
              检测方案冲突...
            </text>
          )}

          {/* 人工审核门禁2 */}
          <HumanReviewGate
            x={600}
            y={400}
            frame={frame}
            delay={review2Active ? 590 : -1000}
            isActive={review2Active}
          />
          <Arrow
            startX={600}
            startY={300}
            endX={600}
            endY={400}
            frame={frame}
            delay={review2Active ? 580 : -1000}
          />
        </g>
      )}

      {/* ===== 阶段三：执行阶段 ===== */}
      {executionPhase && (
        <g>
          {/* 执行重构任务 */}
          <ExecutionTask
            x={300}
            y={300}
            label="重构执行"
            type="refactor"
            frame={frame}
            delay={refactorExecuteActive ? 710 : -1000}
          />

          {/* 测试验证重构 */}
          <AgentNode
            x={500}
            y={300}
            label="测试代理"
            color="#00b894"
            icon="🧪"
            frame={frame}
            delay={refactorTestActive ? 790 : -1000}
            layer="verification"
            status={refactorTestActive ? "active" : refactorTestCompleted ? "completed" : "waiting"}
          />

          {/* 执行性能任务 */}
          <ExecutionTask
            x={700}
            y={300}
            label="性能执行"
            type="performance"
            frame={frame}
            delay={perfExecuteActive ? 830 : -1000}
          />

          {/* 测试验证性能 */}
          <AgentNode
            x={900}
            y={300}
            label="测试代理"
            color="#00b894"
            icon="🧪"
            frame={frame}
            delay={perfTestActive ? 910 : -1000}
            layer="verification"
            status={perfTestActive ? "active" : perfTestCompleted ? "completed" : "waiting"}
          />

          {/* 执行到测试的连接 */}
          <Arrow
            startX={300}
            startY={300}
            endX={500}
            endY={300}
            frame={frame}
            delay={refactorTestActive ? 780 : -1000}
            color="#aaa"
            dashed={true}
          />
          <Arrow
            startX={700}
            startY={300}
            endX={900}
            endY={300}
            frame={frame}
            delay={perfTestActive ? 900 : -1000}
            color="#aaa"
            dashed={true}
          />

          {/* 生成报告指示 */}
          {reportActive && (
            <text x={600} y={250} textAnchor="middle" fill="#00b894" fontSize={14} fontWeight="bold">
              生成执行报告...
            </text>
          )}

          {/* 人工验收门禁3 */}
          <HumanReviewGate
            x={600}
            y={400}
            frame={frame}
            delay={review3Active ? 970 : -1000}
            isActive={review3Active}
          />
          <Arrow
            startX={600}
            startY={300}
            endX={600}
            endY={400}
            frame={frame}
            delay={review3Active ? 960 : -1000}
          />
        </g>
      )}

      {/* 状态显示 */}
      <g transform="translate(50, 750)">
        <text fill="#888" fontSize={12}>
          当前帧: {frame} | 总时长: 1200帧
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