import {
  Absolute,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
} from "remotion";
import { z } from "zod";
import React from "react";

// 状态流转指示器
const StatusIndicator = ({
  x,
  y,
  status,
  label,
}: {
  x: number;
  y: number;
  status: "pending" | "processing" | "completed";
  label: string;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let color = "#9ca3af"; // gray-400
  let text = "待处理";

  if (status === "processing") {
    color = "#3b82f6"; // blue-500
    text = "处理中";
  } else if (status === "completed") {
    color = "#10b981"; // emerald-500
    text = "已完成";
  }

  // 脉冲动画
  const pulseOpacity = interpolate(frame % 60, [0, 30, 60], [0.3, 1, 0.3], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: x - 60,
        top: y + 50,
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}
    >
      <div
        style={{
          width: "12px",
          height: "12px",
          borderRadius: "50%",
          backgroundColor: color,
          opacity: status === "processing" ? pulseOpacity : 1,
          boxShadow: status === "processing" ? `0 0 8px ${color}` : "none",
        }}
      />
      <span style={{ fontSize: "14px", color: "#374151", fontWeight: "500" }}>
        {text}
      </span>
    </div>
  );
};

// 数据包组件
const DataPacket = ({
  x,
  y,
  isVisible,
  label,
}: {
  x: number;
  y: number;
  isVisible: boolean;
  label: string;
}) => {
  if (!isVisible) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: x - 25,
        top: y - 15,
        width: "50px",
        height: "30px",
        backgroundColor: "#dbeafe",
        border: "2px solid #3b82f6",
        borderRadius: "8px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "12px",
        fontWeight: "bold",
        color: "#3b82f6",
        boxShadow: "0 2px 8px rgba(59, 130, 246, 0.3)",
      }}
    >
      {label}
    </div>
  );
};

// 业务规则气泡
const BusinessRuleBubble = ({
  x,
  y,
  text,
  isVisible,
}: {
  x: number;
  y: number;
  text: string;
  isVisible: boolean;
}) => {
  if (!isVisible) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: x - 100,
        top: y - 80,
        backgroundColor: "#fffbeb",
        border: "2px solid #f59e0b",
        borderRadius: "12px",
        padding: "12px",
        maxWidth: "200px",
        fontSize: "14px",
        color: "#92400e",
        boxShadow: "0 4px 12px rgba(245, 158, 11, 0.3)",
        transform: "rotate(-5deg)",
      }}
    >
      {text}
    </div>
  );
};

// 主要的详细动画组件
export const ProjectApprovalFlowDetailed: React.FC<{
  titleText: string;
}> = ({ titleText }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 总时长：450帧（15秒）
  const totalDuration = 450;
  const progress = Math.min(frame / totalDuration, 1);

  // 节点位置
  const centerX = width / 2;
  const nodeY = height / 2 - 50;
  const nodeSpacing = 180;

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

  // 当前步骤计算
  const currentStep = Math.floor(progress * 4);
  const completedSteps = currentStep;

  // 数据包位置动画
  const dataPacketProgress1 = Math.max(0, Math.min((progress - 0.1) / 0.2, 1));
  const dataPacketX1 =
    nodes[0].x + (nodes[1].x - nodes[0].x) * dataPacketProgress1;
  const showDataPacket1 = progress >= 0.1 && progress <= 0.3;

  const dataPacketProgress2 = Math.max(0, Math.min((progress - 0.35) / 0.2, 1));
  const dataPacketX2 =
    nodes[1].x + (nodes[2].x - nodes[1].x) * dataPacketProgress2;
  const showDataPacket2 = progress >= 0.35 && progress <= 0.55;

  const dataPacketProgress3 = Math.max(0, Math.min((progress - 0.6) / 0.2, 1));
  const dataPacketX3 =
    nodes[2].x + (nodes[3].x - nodes[2].x) * dataPacketProgress3;
  const showDataPacket3 = progress >= 0.6 && progress <= 0.8;

  // 业务规则显示时机
  const showRule1 = progress > 0.05 && progress < 0.25;
  const showRule2 = progress > 0.25 && progress < 0.45;
  const showRule3 = progress > 0.45 && progress < 0.65;
  const showRule4 = progress > 0.65 && progress < 0.85;

  return (
    <div
      style={{
        backgroundColor: "#f9fafb",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* 标题 */}
      <div
        style={{
          fontSize: "42px",
          fontWeight: "800",
          color: "#111827",
          marginBottom: "40px",
          textAlign: "center",
          textShadow: "0 2px 4px rgba(0,0,0,0.1)",
        }}
      >
        {titleText}
      </div>

      {/* 副标题 */}
      <div
        style={{
          fontSize: "20px",
          color: "#6b7280",
          marginBottom: "60px",
          textAlign: "center",
        }}
      >
        状态流转 · 数据流向 · 关键业务节点
      </div>

      {/* 流程可视化区域 */}
      <div style={{ position: "relative", width: "100%", height: "450px" }}>
        {/* 连接线 - 使用渐变 */}
        <div
          style={{
            position: "absolute",
            left: nodes[0].x,
            top: nodes[0].y,
            width: nodes[3].x - nodes[0].x,
            height: "4px",
            background:
              "linear-gradient(to right, #9ca3af, #9ca3af, #3b82f6, #10b981, #10b981)",
            clipPath: `inset(0 ${Math.max(0, (1 - progress) * 100)}% 0 0)`,
            borderRadius: "2px",
          }}
        />

        {/* 节点 */}
        {nodes.map((node, index) => {
          const isCompleted = index < completedSteps;
          const isCurrent = index === currentStep;

          let bgColor = "#f3f4f6";
          let textColor = "#6b7280";
          let borderColor = "#d1d5db";
          let shadow = "none";

          if (isCompleted) {
            bgColor = "#dcfce7";
            textColor = "#16a34a";
            borderColor = "#22c55e";
            shadow = "0 4px 12px rgba(34, 197, 94, 0.3)";
          } else if (isCurrent) {
            bgColor = "#dbeafe";
            textColor = "#3b82f6";
            borderColor = "#3b82f6";
            shadow = "0 4px 12px rgba(59, 130, 246, 0.4)";
          }

          // 脉冲效果
          const pulseScale = isCurrent
            ? interpolate(frame % 60, [0, 30, 60], [1, 1.1, 1])
            : 1;

          return (
            <div
              key={node.key}
              style={{
                position: "absolute",
                left: node.x - 60,
                top: node.y - 60,
                width: "120px",
                height: "120px",
                backgroundColor: bgColor,
                borderRadius: "50%",
                border: `3px solid ${borderColor}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transform: `scale(${pulseScale})`,
                boxShadow: shadow,
                transition: "all 0.3s ease",
              }}
            >
              <div
                style={{
                  textAlign: "center",
                  fontSize: "16px",
                  fontWeight: "700",
                  color: textColor,
                  lineHeight: "1.3",
                }}
              >
                {node.text}
              </div>
            </div>
          );
        })}

        {/* 状态指示器 */}
        {nodes.map((node, index) => (
          <StatusIndicator
            key={`status-${node.key}`}
            x={node.x}
            y={node.y}
            status={
              index < completedSteps
                ? "completed"
                : index === currentStep
                  ? "processing"
                  : "pending"
            }
            label={node.text}
          />
        ))}

        {/* 数据包 */}
        <DataPacket
          x={dataPacketX1}
          y={nodeY - 40}
          isVisible={showDataPacket1}
          label="申请数据"
        />
        <DataPacket
          x={dataPacketX2}
          y={nodeY - 40}
          isVisible={showDataPacket2}
          label="预算确认"
        />
        <DataPacket
          x={dataPacketX3}
          y={nodeY - 40}
          isVisible={showDataPacket3}
          label="审批结果"
        />

        {/* 业务规则气泡 */}
        <BusinessRuleBubble
          x={nodes[0].x}
          y={nodes[0].y}
          text="支持独立项目和项目集立项，包含预算信息、执行信息等"
          isVisible={showRule1}
        />
        <BusinessRuleBubble
          x={nodes[1].x}
          y={nodes[1].y}
          text="财务确认预算来源、金额、税率，验证预算可用性"
          isVisible={showRule2}
        />
        <BusinessRuleBubble
          x={nodes[2].x}
          y={nodes[2].y}
          text="动态审批流程，根据预算部门和金额确定审批人"
          isVisible={showRule3}
        />
        <BusinessRuleBubble
          x={nodes[3].x}
          y={nodes[3].y}
          text="审批通过后创建正式项目，同步预算到ERP系统"
          isVisible={showRule4}
        />
      </div>

      {/* 底部说明 */}
      <div
        style={{
          position: "absolute",
          bottom: "40px",
          width: "90%",
          textAlign: "center",
          fontSize: "16px",
          color: "#4b5563",
          backgroundColor: "rgba(255, 255, 255, 0.95)",
          padding: "16px",
          borderRadius: "12px",
          border: "1px solid #e5e7eb",
          backdropFilter: "blur(10px)",
        }}
      >
        <strong>核心业务规则：</strong>
        预算预占机制 · 状态机流转 · 权限控制 · 数据一致性保障
      </div>
    </div>
  );
};

// 定义组件的props schema
export const ProjectApprovalFlowDetailedSchema = z.object({
  titleText: z.string().default("立项审批流程 - 详细版"),
});
