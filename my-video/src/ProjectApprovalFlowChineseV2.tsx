import { useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

// 中文版立项审批流程动画 V2 - 完全基于真实业务逻辑

// 第一阶段：数据结构与参数校验 (0-3秒)
const DataStructureAndValidation = ({
  progress,
  width,
  height,
}: {
  progress: number;
  width: number;
  height: number;
}) => {
  const centerX = width / 2;
  const startY = height / 2 - 100;

  // 阶段进度: 0-0.25
  const sectionProgress = Math.min(progress / 0.25, 1);

  // 真实的API调用链
  const apiCallChain = [
    {
      method: "POST /logan/dragon/mmp/project/application/save",
      desc: "前端HTTP请求",
      type: "http",
    },
    {
      method: "ProjectApplicationController.saveProjectApplication()",
      desc: "Controller接收请求",
      type: "controller",
    },
    {
      method: "ProjectApplicationService.addProjectApplication()",
      desc: "核心业务逻辑",
      type: "service",
    },
    {
      method: "SequenceGenerationService.generateApplicationNo()",
      desc: "生成唯一立项单号",
      type: "util",
    },
    {
      method: "ProjectBudgetInfoService.createBudgetInfos()",
      desc: "创建多维度预算信息",
      type: "service",
    },
    {
      method: "FlowBootService.submitFlow() (if operateType=SUBMIT)",
      desc: "提交审批流程(仅当operateType=1)",
      type: "external",
    },
  ];

  const visibleCalls = Math.floor(sectionProgress * apiCallChain.length);

  const callNodes = apiCallChain.map((call, index) => {
    const y = startY + (index - 2.5) * 60;
    const isActive = index <= visibleCalls;
    const isCurrent = index === visibleCalls && sectionProgress < 1;

    let bgColor = "#f3f4f6";
    let borderColor = "#d1d5db";
    if (isActive) {
      if (isCurrent) {
        bgColor = "#dbeafe";
        borderColor = "#3b82f6";
      } else {
        bgColor = "#dcfce7";
        borderColor = "#10b981";
      }
    }

    let color = "#6b7280";
    if (call.type === "http") color = "#ef4444";
    else if (call.type === "controller") color = "#f59e0b";
    else if (call.type === "service") color = "#3b82f6";
    else if (call.type === "util") color = "#8b5cf6";
    else if (call.type === "external") color = "#ec4899";

    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: centerX - 300,
          top: y - 25,
          width: 600,
          height: 50,
          backgroundColor: bgColor,
          border: `2px solid ${borderColor}`,
          borderRadius: "12px",
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          transform: isCurrent ? "scale(1.05)" : "scale(1)",
          boxShadow: isCurrent ? "0 0 15px rgba(59, 130, 246, 0.5)" : "none",
          transition: "all 0.3s ease",
        }}
      >
        <span
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            color: color,
            flex: 1,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {call.method}
        </span>
        <span
          style={{
            fontSize: "10px",
            color: "#6b7280",
            backgroundColor: "#f1f5f9",
            padding: "2px 6px",
            borderRadius: "6px",
            marginLeft: "8px",
          }}
        >
          {call.desc}
        </span>
      </div>
    );
  });

  // operateType说明
  const operateTypeVisible = sectionProgress > 0.6;
  const operateTypeElement = operateTypeVisible && (
    <div
      style={{
        position: "absolute",
        left: centerX - 150,
        top: startY + 200,
        width: 300,
        backgroundColor: "#fff3cd",
        border: "2px solid #ffc107",
        borderRadius: "12px",
        padding: "12px",
        fontSize: "14px",
        color: "#856404",
        textAlign: "center",
        fontWeight: "bold",
        boxShadow: "0 4px 12px rgba(255, 193, 7, 0.3)",
      }}
    >
      ⚠️ operateType参数区分：
      <br />
      <span style={{ color: "#dc3545" }}>0 = 保存草稿</span> |{" "}
      <span style={{ color: "#28a745" }}>1 = 提交审批</span>
    </div>
  );

  return (
    <div>
      {callNodes}
      {operateTypeElement}
      <div
        style={{
          position: "absolute",
          left: centerX - 150,
          top: startY - 200,
          fontSize: "22px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
          textShadow: "0 2px 4px rgba(0,0,0,0.3)",
        }}
      >
        数据结构与参数校验 (真实API调用链)
      </div>
    </div>
  );
};

// 第二阶段：真实项目状态机 (3-6秒)
const RealProjectStateMachine = ({
  progress,
  width,
  height,
}: {
  progress: number;
  width: number;
  height: number;
}) => {
  const centerX = width / 2;
  const centerY = height / 2;

  // 阶段进度: 0.25-0.5
  const sectionProgress = Math.min(Math.max((progress - 0.25) / 0.25, 0), 1);

  // 真实的7种项目状态
  const projectStates = [
    { code: 0, name: "ALREADY_APPLICATION", desc: "进行中", color: "#3b82f6" },
    { code: -1, name: "WAIT_CLOSE", desc: "待关闭", color: "#f59e0b" },
    { code: 1, name: "CLOSED", desc: "ERP结算中", color: "#8b5cf6" },
    { code: 4, name: "SETTLING", desc: "骁龙结算中", color: "#ec4899" },
    { code: 7, name: "SETTLE_FAILED", desc: "结算失败", color: "#ef4444" },
    { code: 2, name: "END", desc: "已结束", color: "#10b981" },
    { code: 3, name: "CANCELED", desc: "已取消", color: "#6b7280" },
  ];

  // 状态流转规则
  const stateTransitions = [
    { from: 0, to: -1, condition: "发起关闭", guard: "关闭校验通过" },
    { from: 0, to: 3, condition: "取消项目", guard: "审批通过" },
    { from: -1, to: 4, condition: "发起结算", guard: "WBS全部完成" },
    { from: 4, to: 1, condition: "ERP结算中", guard: "" },
    { from: 4, to: 7, condition: "结算失败", guard: "" },
    { from: 1, to: 2, condition: "ERP结算完成", guard: "" },
    { from: 7, to: 4, condition: "重新结算", guard: "" },
  ];

  // 计算当前激活的状态和转换
  const activeStateIndex = Math.floor(sectionProgress * projectStates.length);
  const activeTransitionIndex = Math.floor(
    sectionProgress * stateTransitions.length,
  );

  // 渲染状态节点 - 环形布局
  const stateNodes = projectStates.map((state, index) => {
    const angle = (index / projectStates.length) * 2 * Math.PI - Math.PI / 2;
    const radius = 160;
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;
    const isActive = index <= activeStateIndex;

    return (
      <div
        key={state.code}
        style={{
          position: "absolute",
          left: x - 55,
          top: y - 35,
          width: 110,
          height: 70,
          backgroundColor: isActive ? state.color : "#f3f4f6",
          border: `2px solid ${isActive ? state.color : "#d1d5db"}`,
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          opacity: isActive ? 1 : 0.6,
          transform: isActive ? "scale(1.1)" : "scale(1)",
          boxShadow: isActive ? `0 0 15px ${state.color}80` : "none",
          transition: "all 0.3s ease",
        }}
      >
        <span style={{ fontSize: "12px", fontWeight: "bold", color: "white" }}>
          {state.desc}
        </span>
        <span style={{ fontSize: "10px", color: "white", opacity: 0.8 }}>
          状态码: {state.code}
        </span>
        <span style={{ fontSize: "8px", color: "white", opacity: 0.6 }}>
          {state.name}
        </span>
      </div>
    );
  });

  // 渲染状态转换箭头和条件
  const transitionElements = stateTransitions
    .slice(0, activeTransitionIndex + 1)
    .map((transition, index) => {
      const fromState = projectStates.find((s) => s.code === transition.from);
      const toState = projectStates.find((s) => s.code === transition.to);

      if (!fromState || !toState) return null;

      const fromAngle =
        (projectStates.findIndex((s) => s.code === transition.from) /
          projectStates.length) *
          2 *
          Math.PI -
        Math.PI / 2;
      const toAngle =
        (projectStates.findIndex((s) => s.code === transition.to) /
          projectStates.length) *
          2 *
          Math.PI -
        Math.PI / 2;
      const radius = 160;

      const fromX = centerX + Math.cos(fromAngle) * radius;
      const fromY = centerY + Math.sin(fromAngle) * radius;
      const toX = centerX + Math.cos(toAngle) * radius;
      const toY = centerY + Math.sin(toAngle) * radius;

      // 计算中间点
      const midX = (fromX + toX) / 2;
      const midY = (fromY + toY) / 2;

      return (
        <div
          key={index}
          style={{
            position: "absolute",
            left: midX - 70,
            top: midY - 20,
            backgroundColor: "#ffffff",
            border: "2px solid #3b82f6",
            borderRadius: "8px",
            padding: "6px 10px",
            fontSize: "11px",
            color: "#374151",
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
            maxWidth: "140px",
            textAlign: "center",
          }}
        >
          <div style={{ fontWeight: "bold", color: "#3b82f6" }}>
            {transition.condition}
          </div>
          {transition.guard && (
            <div style={{ fontSize: "9px", color: "#6b7280" }}>
              {transition.guard}
            </div>
          )}
        </div>
      );
    });

  // 关键说明
  const keyNotes = [
    "⚠️ 项目实体使用Integer类型存储状态值",
    "✅ 建议通过ProjectStatusEnum枚举类访问状态",
    "🔄 状态流转有严格的守卫条件",
    "📊 WBS完成度是关键校验点",
  ];

  const noteElements = keyNotes.map((note, index) => {
    const isVisible = sectionProgress > index * 0.25;
    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: centerX - 200,
          top: centerY + 220 + index * 22,
          fontSize: "13px",
          color: isVisible ? "#10b981" : "#9ca3af",
          fontWeight: isVisible ? "bold" : "normal",
          opacity: isVisible ? 1 : 0.5,
          transition: "all 0.3s ease",
        }}
      >
        {note}
      </div>
    );
  });

  return (
    <div>
      {stateNodes}
      {transitionElements}
      {noteElements}
      <div
        style={{
          position: "absolute",
          left: centerX - 180,
          top: centerY - 240,
          fontSize: "22px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
          textShadow: "0 2px 4px rgba(0,0,0,0.3)",
        }}
      >
        真实项目状态机 (7种状态 + 守卫条件)
      </div>
    </div>
  );
};

// 第三阶段：异步Kafka处理与ERP同步 (6-9秒)
const AsyncKafkaAndErpSync = ({
  progress,
  width,
  height,
}: {
  progress: number;
  width: number;
  height: number;
}) => {
  const centerX = width / 2;
  const centerY = height / 2;

  // 阶段进度: 0.5-0.75
  const sectionProgress = Math.min(Math.max((progress - 0.5) / 0.25, 0), 1);

  // 异步处理流程
  const asyncFlow = [
    { step: "审批通过", desc: "审批系统返回通过结果", time: 0 },
    { step: "Kafka发送", desc: "发送dragon_work_flow_result消息", time: 0.2 },
    {
      step: "消息消费",
      desc: "ProjectApplicationProcessResultHandler.onSuccess()",
      time: 0.4,
    },
    {
      step: "ERP同步",
      desc: "ErpBudgetSyncService.syncProjectBudget()",
      time: 0.6,
    },
    { step: "完成", desc: "项目立项完成", time: 0.8 },
  ];

  const flowElements = asyncFlow.map((step, index) => {
    const x = centerX + (index - 2) * 140;
    const y = centerY - 50;
    const isCompleted = sectionProgress > step.time + 0.1;
    const isInProgress = sectionProgress > step.time && !isCompleted;

    let bgColor = "#f3f4f6";
    let borderColor = "#d1d5db";
    let textColor = "#6b7280";

    if (isCompleted) {
      bgColor = "#dcfce7";
      borderColor = "#10b981";
      textColor = "#10b981";
    } else if (isInProgress) {
      bgColor = "#dbeafe";
      borderColor = "#3b82f6";
      textColor = "#3b82f6";
    }

    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: x - 60,
          top: y - 30,
          width: 120,
          height: 60,
          backgroundColor: bgColor,
          border: `2px solid ${borderColor}`,
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          transform: isInProgress ? "scale(1.1)" : "scale(1)",
          boxShadow: isInProgress ? "0 0 15px rgba(59, 130, 246, 0.5)" : "none",
          transition: "all 0.3s ease",
        }}
      >
        <span
          style={{ fontSize: "14px", fontWeight: "bold", color: textColor }}
        >
          {step.step}
        </span>
        {isCompleted || isInProgress ? (
          <span
            style={{
              fontSize: "9px",
              color: "#6b7280",
              textAlign: "center",
              lineHeight: "1.2",
            }}
          >
            {step.desc}
          </span>
        ) : null}
      </div>
    );
  });

  // 连接线
  const connectionLines = [];
  for (let i = 0; i < 4; i++) {
    const x1 = centerX + (i - 2) * 140 + 60;
    const x2 = centerX + (i - 1) * 140 - 60;
    const y = centerY - 50;
    const isCompleted = sectionProgress > asyncFlow[i].time + 0.1;

    connectionLines.push(
      <div
        key={i}
        style={{
          position: "absolute",
          left: x1,
          top: y - 2,
          width: x2 - x1,
          height: "4px",
          backgroundColor: isCompleted ? "#10b981" : "#d1d5db",
          borderRadius: "2px",
        }}
      />,
    );
  }

  // 关键纠正说明
  const correctionNotes = [
    "❌ 错误认知：ERP同步在创建申请时调用",
    "✅ 正确认知：ERP同步在审批通过后通过Kafka异步触发",
    "🔄 Kafka Topic: dragon_work_flow_result",
    "⏰ 异步处理确保系统高可用性",
  ];

  const correctionElements = correctionNotes.map((note, index) => {
    const isVisible = sectionProgress > 0.5 + index * 0.125;
    const isError = note.startsWith("❌");
    const isCorrect = note.startsWith("✅");

    let color = "#9ca3af";
    if (isError) color = "#ef4444";
    else if (isCorrect) color = "#10b981";

    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: centerX - 250,
          top: centerY + 120 + index * 25,
          fontSize: "14px",
          color: isVisible ? color : "#9ca3af",
          fontWeight: isVisible ? "bold" : "normal",
          opacity: isVisible ? 1 : 0.5,
          transition: "all 0.3s ease",
        }}
      >
        {note}
      </div>
    );
  });

  return (
    <div>
      {connectionLines}
      {flowElements}
      {correctionElements}
      <div
        style={{
          position: "absolute",
          left: centerX - 200,
          top: centerY - 150,
          fontSize: "22px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
          textShadow: "0 2px 4px rgba(0,0,0,0.3)",
        }}
      >
        异步Kafka处理与ERP同步 (纠正错误认知)
      </div>
    </div>
  );
};

// 第四阶段：业务规则、风险控制与最佳实践 (9-12秒)
const BusinessRulesAndBestPractices = ({
  progress,
  width,
  height,
}: {
  progress: number;
  width: number;
  height: number;
}) => {
  const centerX = width / 2;
  const centerY = height / 2;

  // 阶段进度: 0.75-1.0
  const sectionProgress = Math.min(Math.max((progress - 0.75) / 0.25, 0), 1);

  // 业务规则分类
  const businessCategories = [
    {
      title: "预算管理规则",
      icon: "💰",
      items: [
        "部门钱包(DEP_BUDGET): 支持调增调减，需完整审批",
        "直营门店(SHOP_BUDGET): 支持调增调减，需成本中心同步",
        "授权自筹(SELF_BUDGET): 不支持调增调减，无ERP同步",
        "调减金额不能超过可调减余额，调减后剩余金额≥0",
      ],
    },
    {
      title: "关闭校验规则",
      icon: "🔒",
      items: [
        "WBS必须100%完成才能发起关闭",
        "未核销活动必须处理完毕",
        "预算使用情况需要完整验证",
        "关闭校验通过才能进入结算流程",
      ],
    },
    {
      title: "风险控制措施",
      icon: "🛡️",
      items: [
        "预算超占风险: 分布式锁控制并发",
        "ERP同步失败: 重试机制+补偿逻辑",
        "状态机异常: 日志监控+异常拦截",
        "精度漂移问题: BigDecimal显式舍入模式",
      ],
    },
    {
      title: "最佳实践建议",
      icon: "⭐",
      items: [
        "使用ProjectStatusEnum枚举类访问状态",
        "事务边界内避免同步远程调用",
        "批量操作减少数据库交互",
        "完善日志记录便于问题追踪",
      ],
    },
  ];

  const visibleCategories = Math.floor(
    sectionProgress * businessCategories.length,
  );

  const categoryCards = businessCategories
    .slice(0, visibleCategories + 1)
    .map((category, index) => {
      const positions = [
        { x: -200, y: -120 }, // 左上
        { x: 200, y: -120 }, // 右上
        { x: -200, y: 120 }, // 左下
        { x: 200, y: 120 }, // 右下
      ];

      const pos = positions[index];
      const cardOpacity =
        index === visibleCategories ? sectionProgress * 4 - index : 1;

      return (
        <div
          key={index}
          style={{
            position: "absolute",
            left: centerX + pos.x - 160,
            top: centerY + pos.y - 100,
            width: 320,
            backgroundColor: "#f8fafc",
            border: "3px solid #3b82f6",
            borderRadius: "16px",
            padding: "20px",
            boxShadow: "0 6px 16px rgba(0,0,0,0.25)",
            opacity: cardOpacity,
            transform: `scale(${0.7 + cardOpacity * 0.3}) rotate(${cardOpacity * 5}deg)`,
            transition: "all 0.4s ease",
          }}
        >
          <div
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              color: "#3b82f6",
              marginBottom: "16px",
              textAlign: "center",
              borderBottom: "3px solid #3b82f6",
              paddingBottom: "12px",
            }}
          >
            {category.icon} {category.title}
          </div>
          <ul
            style={{
              fontSize: "13px",
              color: "#475569",
              paddingLeft: "24px",
              margin: "0",
              lineHeight: "1.6",
            }}
          >
            {category.items.map((item, itemIndex) => (
              <li key={itemIndex} style={{ marginBottom: "8px" }}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      );
    });

  return (
    <div>
      {categoryCards}
      <div
        style={{
          position: "absolute",
          left: centerX - 220,
          top: 50,
          fontSize: "26px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
          textShadow: "0 2px 8px rgba(0,0,0,0.5)",
        }}
      >
        业务规则、风险控制与最佳实践
      </div>
    </div>
  );
};

// 主组件
export const ProjectApprovalFlowChineseV2: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // 总时长：360帧 (12秒 @ 30fps)
  const totalDuration = 360;
  const progress = Math.min(frame / totalDuration, 1);

  // 确定当前阶段
  let currentSection = 1;
  if (progress > 0.25) currentSection = 2;
  if (progress > 0.5) currentSection = 3;
  if (progress > 0.75) currentSection = 4;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        backgroundColor: "black",
      }}
    >
      {/* 背景渐变 */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
        }}
      />

      {/* 标题 - 强调技术准确性 */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: "26px",
          fontWeight: "bold",
          color: "white",
          textShadow: "0 2px 8px rgba(0,0,0,0.5)",
          lineHeight: "1.3",
        }}
      >
        立项审批流程 - 技术准确版
        <div
          style={{
            fontSize: "16px",
            fontWeight: "normal",
            marginTop: "8px",
            color: "#94a3b8",
          }}
        >
          基于真实业务逻辑 · 纠正错误认知 · 展示最佳实践
        </div>
      </div>

      {/* 进度条 */}
      <div
        style={{
          position: "absolute",
          bottom: 20,
          left: 50,
          right: 50,
          height: "8px",
          backgroundColor: "#334155",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress * 100}%`,
            backgroundColor: "#3b82f6",
            transition: "width 0.1s ease",
          }}
        />
      </div>

      {/* 阶段指示器 */}
      {[1, 2, 3, 4].map((section) => {
        const sectionNames = ["数据校验", "状态机", "异步处理", "业务规则"];
        const isActive = section === currentSection;
        const isCompleted = section < currentSection;

        return (
          <div
            key={section}
            style={{
              position: "absolute",
              bottom: 40,
              left: 120 + (section - 1) * 130,
              width: 100,
              height: 30,
              backgroundColor: isCompleted
                ? "#10b981"
                : isActive
                  ? "#3b82f6"
                  : "#64748b",
              borderRadius: "15px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "12px",
              fontWeight: "bold",
              color: "white",
            }}
          >
            {sectionNames[section - 1]}
          </div>
        );
      })}

      {/* 渲染当前阶段 */}
      {currentSection === 1 && (
        <DataStructureAndValidation
          progress={progress}
          width={width}
          height={height}
        />
      )}
      {currentSection === 2 && (
        <RealProjectStateMachine
          progress={progress}
          width={width}
          height={height}
        />
      )}
      {currentSection === 3 && (
        <AsyncKafkaAndErpSync
          progress={progress}
          width={width}
          height={height}
        />
      )}
      {currentSection === 4 && (
        <BusinessRulesAndBestPractices
          progress={progress}
          width={width}
          height={height}
        />
      )}
    </div>
  );
};
