import {
  Absolute,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import React from "react";

// 定义流程节点的类型
const Node = ({
  x,
  y,
  text,
  status,
  isCurrent,
  isCompleted,
}: {
  x: number;
  y: number;
  text: string;
  status: "pending" | "active" | "completed";
  isCurrent: boolean;
  isCompleted: boolean;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 节点大小和颜色
  const size = 80;
  let bgColor = "#f3f4f6"; // 灰色 - 待处理
  let textColor = "#6b7280";
  let borderColor = "#d1d5db";

  if (isCompleted) {
    bgColor = "#dcfce7"; // 绿色 - 已完成
    textColor = "#16a34a";
    borderColor = "#22c55e";
  } else if (isCurrent) {
    bgColor = "#dbeafe"; // 蓝色 - 当前步骤
    textColor = "#3b82f6";
    borderColor = "#3b82f6";
  }

  // 添加脉冲效果到当前节点
  const pulseScale = interpolate(frame, [0, 30], [1, 1.1], {
    extrapolateRight: "clamp",
  });

  const scale = isCurrent ? pulseScale : 1;

  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        backgroundColor: bgColor,
        borderRadius: "50%",
        border: `3px solid ${borderColor}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        boxShadow: isCurrent ? "0 0 20px rgba(59, 130, 246, 0.5)" : "none",
        transition: "all 0.3s ease",
      }}
    >
      <div
        style={{
          textAlign: "center",
          fontSize: "14px",
          fontWeight: "bold",
          color: textColor,
          lineHeight: "1.2",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// 连接线组件
const ConnectionLine = ({
  x1,
  y1,
  x2,
  y2,
  isCompleted,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  isCompleted: boolean;
}) => {
  const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  const angle = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;

  return (
    <div
      style={{
        position: "absolute",
        left: x1,
        top: y1,
        width: length,
        height: 3,
        backgroundColor: isCompleted ? "#22c55e" : "#d1d5db",
        transform: `rotate(${angle}deg)`,
        transformOrigin: "left center",
        transition: "background-color 0.3s ease",
      }}
    />
  );
};

// 数据流向箭头
const DataFlowArrow = ({
  x,
  y,
  direction,
  isVisible,
}: {
  x: number;
  y: number;
  direction: "right" | "down";
  isVisible: boolean;
}) => {
  if (!isVisible) return null;

  const rotation = direction === "right" ? 0 : 90;

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 20,
        height: 20,
        opacity: isVisible ? 1 : 0,
        transition: "opacity 0.3s ease",
      }}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        style={{ transform: `rotate(${rotation}deg)` }}
      >
        <path
          d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"
          fill="#3b82f6"
        />
      </svg>
    </div>
  );
};

// 主要的动画组件
export const ProjectApprovalFlow: React.FC<{
  titleText: string;
}> = ({ titleText }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 计算当前进度 (假设总时长为300帧，约10秒)
  const totalDuration = 300;
  const progress = Math.min(frame / totalDuration, 1);

  // 定义四个节点的位置
  const centerX = width / 2;
  const nodeY = height / 2;
  const nodeSpacing = 200;

  const nodes = [
    {
      x: centerX - nodeSpacing * 1.5,
      y: nodeY,
      text: "项目申请",
      key: "application",
    },
    {
      x: centerX - nodeSpacing * 0.5,
      y: nodeY,
      text: "财务确认",
      key: "finance",
    },
    {
      x: centerX + nodeSpacing * 0.5,
      y: nodeY,
      text: "审批流",
      key: "approval",
    },
    {
      x: centerX + nodeSpacing * 1.5,
      y: nodeY,
      text: "项目创建",
      key: "creation",
    },
  ];

  // 根据进度确定当前激活的节点
  const currentStep = Math.floor(progress * 4);
  const completedSteps = currentStep;

  // 数据流向的显示时机
  const showDataFlow1 = progress > 0.1 && progress < 0.3;
  const showDataFlow2 = progress > 0.35 && progress < 0.55;
  const showDataFlow3 = progress > 0.6 && progress < 0.8;

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* 标题 */}
      <div
        style={{
          fontSize: "48px",
          fontWeight: "bold",
          color: "#1f2937",
          marginBottom: "60px",
          textAlign: "center",
        }}
      >
        {titleText}
      </div>

      {/* 流程节点和连线 */}
      <div style={{ position: "relative", width: "100%", height: "400px" }}>
        {/* 连接线 */}
        <ConnectionLine
          x1={nodes[0].x}
          y1={nodes[0].y}
          x2={nodes[1].x}
          y2={nodes[1].y}
          isCompleted={completedSteps >= 1}
        />
        <ConnectionLine
          x1={nodes[1].x}
          y1={nodes[1].y}
          x2={nodes[2].x}
          y2={nodes[2].y}
          isCompleted={completedSteps >= 2}
        />
        <ConnectionLine
          x1={nodes[2].x}
          y1={nodes[2].y}
          x2={nodes[3].x}
          y2={nodes[3].y}
          isCompleted={completedSteps >= 3}
        />

        {/* 数据流向箭头 */}
        <DataFlowArrow
          x={nodes[0].x + 60}
          y={nodes[0].y - 15}
          direction="right"
          isVisible={showDataFlow1}
        />
        <DataFlowArrow
          x={nodes[1].x + 60}
          y={nodes[1].y - 15}
          direction="right"
          isVisible={showDataFlow2}
        />
        <DataFlowArrow
          x={nodes[2].x + 60}
          y={nodes[2].y - 15}
          direction="right"
          isVisible={showDataFlow3}
        />

        {/* 节点 */}
        {nodes.map((node, index) => (
          <Node
            key={node.key}
            x={node.x}
            y={node.y}
            text={node.text}
            status={
              index < completedSteps
                ? "completed"
                : index === currentStep
                  ? "active"
                  : "pending"
            }
            isCurrent={index === currentStep}
            isCompleted={index < completedSteps}
          />
        ))}
      </div>

      {/* 关键业务节点说明 */}
      <div
        style={{
          position: "absolute",
          bottom: "80px",
          width: "80%",
          textAlign: "center",
          fontSize: "20px",
          color: "#6b7280",
          backgroundColor: "rgba(255, 255, 255, 0.9)",
          padding: "20px",
          borderRadius: "10px",
          border: "2px solid #e5e7eb",
        }}
      >
        {currentStep === 0 && "用户提交项目申请，包含预算信息、执行信息等"}
        {currentStep === 1 && "财务人员确认预算信息，验证预算来源和金额"}
        {currentStep === 2 && "根据预算部门和金额动态确定审批人，发起审批流程"}
        {currentStep === 3 && "审批通过后自动创建正式项目，同步预算到ERP系统"}
      </div>
    </div>
  );
};

// 定义组件的props schema
export const ProjectApprovalFlowSchema = z.object({
  titleText: z.string().default("立项审批流程"),
});
