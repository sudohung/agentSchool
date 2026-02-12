import { useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import React from "react";

// Data structure validation component
const DataStructureValidation = ({
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

  // Show validation steps based on progress within section 1 (0-0.25)
  const sectionProgress = Math.min(progress / 0.25, 1);
  const currentStep = Math.floor(sectionProgress * 4);

  const validationSteps = [
    {
      name: "Schema Validation",
      desc: "Validate JSON schema against DTO",
      icon: "📋",
    },
    {
      name: "Budget Check",
      desc: "Verify budget amount and source",
      icon: "💰",
    },
    { name: "Permission Check", desc: "Validate user permissions", icon: "🔑" },
    {
      name: "Data Integrity",
      desc: "Ensure all required fields present",
      icon: "✅",
    },
  ];

  const stepNodes = validationSteps.map((step, index) => {
    const x = centerX + (index - 1.5) * 150;
    const y = startY;
    const isActive = index <= currentStep;
    const isCurrent = index === currentStep && sectionProgress < 1;

    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: x - 40,
          top: y - 40,
          width: 80,
          height: 80,
          backgroundColor: isActive
            ? isCurrent
              ? "#dbeafe"
              : "#dcfce7"
            : "#f3f4f6",
          border: `3px solid ${isActive ? (isCurrent ? "#3b82f6" : "#22c55e") : "#d1d5db"}`,
          borderRadius: "50%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          transform: isCurrent ? "scale(1.1)" : "scale(1)",
          boxShadow: isCurrent ? "0 0 20px rgba(59, 130, 246, 0.5)" : "none",
          transition: "all 0.3s ease",
        }}
      >
        <span style={{ fontSize: "24px", marginBottom: "4px" }}>
          {step.icon}
        </span>
        <span
          style={{
            fontSize: "10px",
            textAlign: "center",
            fontWeight: "bold",
            color: isActive ? (isCurrent ? "#3b82f6" : "#16a34a") : "#6b7280",
          }}
        >
          {step.name}
        </span>
      </div>
    );
  });

  // Connection lines between steps
  const connectionLines = [];
  for (let i = 0; i < 3; i++) {
    const x1 = centerX + (i - 1.5) * 150 + 40;
    const x2 = centerX + (i - 0.5) * 150 - 40;
    const y = startY;
    const isCompleted = i < currentStep;

    connectionLines.push(
      <div
        key={i}
        style={{
          position: "absolute",
          left: x1,
          top: y - 2,
          width: x2 - x1,
          height: "4px",
          backgroundColor: isCompleted ? "#22c55e" : "#d1d5db",
          borderRadius: "2px",
        }}
      />,
    );
  }

  return (
    <div>
      {connectionLines}
      {stepNodes}
      <div
        style={{
          position: "absolute",
          left: centerX - 100,
          top: startY + 100,
          fontSize: "18px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
        }}
      >
        Data Structure Validation
      </div>
    </div>
  );
};

// Status transition component
const StatusTransition = ({
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

  // Section 2: 0.25-0.5
  const sectionProgress = Math.min(Math.max((progress - 0.25) / 0.25, 0), 1);

  const statuses = [
    { name: "DRAFT", color: "#9ca3af", desc: "Initial state" },
    { name: "PENDING", color: "#3b82f6", desc: "Awaiting review" },
    { name: "APPROVED", color: "#10b981", desc: "Ready for processing" },
    { name: "COMPLETED", color: "#8b5cf6", desc: "Final state" },
  ];

  // Current status index
  const currentStatusIndex = Math.floor(sectionProgress * 3);
  const nextStatusIndex = Math.min(currentStatusIndex + 1, 3);
  const transitionProgress = (sectionProgress * 3) % 1;

  // Status nodes
  const statusNodes = statuses.map((status, index) => {
    const x = centerX + (index - 1.5) * 120;
    const y = centerY - 50;
    const isActive =
      index <= currentStatusIndex ||
      (index === nextStatusIndex && transitionProgress > 0);
    const isCurrent = index === currentStatusIndex;
    const isNext = index === nextStatusIndex;

    let opacity = 1;
    if (isNext) {
      opacity = transitionProgress;
    } else if (index > nextStatusIndex) {
      opacity = 0.3;
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
          backgroundColor: isActive ? status.color : "#f3f4f6",
          border: `2px solid ${isActive ? status.color : "#d1d5db"}`,
          borderRadius: "12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: opacity,
          transform: isCurrent ? "scale(1.1)" : "scale(1)",
          boxShadow: isCurrent ? `0 0 15px ${status.color}` : "none",
          transition: "all 0.3s ease",
        }}
      >
        <span
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            color: "white",
          }}
        >
          {status.name}
        </span>
      </div>
    );
  });

  // Transition arrow
  if (currentStatusIndex < 3) {
    const fromX = centerX + (currentStatusIndex - 1.5) * 120 + 60;
    const toX = centerX + (nextStatusIndex - 1.5) * 120 - 60;
    const arrowX = fromX + (toX - fromX) * transitionProgress;

    statusNodes.push(
      <div
        key="arrow"
        style={{
          position: "absolute",
          left: arrowX - 10,
          top: centerY - 45,
          fontSize: "24px",
          opacity: transitionProgress > 0 ? 1 : 0,
        }}
      >
        →
      </div>,
    );
  }

  return (
    <div>
      {statusNodes}
      <div
        style={{
          position: "absolute",
          left: centerX - 80,
          top: centerY + 50,
          fontSize: "18px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
        }}
      >
        Status Transition Flow
      </div>
    </div>
  );
};

// Kafka async processing component
const KafkaAsyncProcessing = ({
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

  // Section 3: 0.5-0.75
  const sectionProgress = Math.min(Math.max((progress - 0.5) / 0.25, 0), 1);

  // Kafka topics
  const topics = [
    "project-submission",
    "approval-events",
    "notification-queue",
  ];

  // Messages moving through the system
  const messageCount = 5;
  const messages = [];

  for (let i = 0; i < messageCount; i++) {
    const messageProgress = Math.min((sectionProgress + i * 0.2) % 1.2, 1);
    if (messageProgress > 0 && messageProgress <= 1) {
      const topicIndex = Math.floor(messageProgress * 3) % 3;
      const topicProgress = (messageProgress * 3) % 1;

      const startX = centerX - 200;
      const endX = centerX + 200;
      const x = startX + (endX - startX) * topicProgress;
      const y = centerY - 100 + topicIndex * 50;

      messages.push(
        <div
          key={i}
          style={{
            position: "absolute",
            left: x - 15,
            top: y - 10,
            width: 30,
            height: 20,
            backgroundColor: "#fbbf24",
            border: "2px solid #f59e0b",
            borderRadius: "4px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "12px",
            fontWeight: "bold",
            color: "#7c2d12",
            boxShadow: "0 2px 8px rgba(251, 191, 36, 0.5)",
          }}
        >
          📦
        </div>,
      );
    }
  }

  // Topic labels
  const topicLabels = topics.map((topic, index) => {
    const y = centerY - 100 + index * 50;
    const isActive = sectionProgress > 0.1 * index;

    return (
      <div
        key={index}
        style={{
          position: "absolute",
          left: centerX - 250,
          top: y - 15,
          fontSize: "14px",
          fontWeight: "bold",
          color: isActive ? "#3b82f6" : "#9ca3af",
          backgroundColor: isActive ? "#dbeafe" : "#f3f4f6",
          padding: "4px 8px",
          borderRadius: "8px",
          border: `2px solid ${isActive ? "#3b82f6" : "#d1d5db"}`,
        }}
      >
        {topic}
      </div>
    );
  });

  // Kafka cluster visualization
  const kafkaCluster = (
    <div
      style={{
        position: "absolute",
        left: centerX - 80,
        top: centerY + 80,
        width: 160,
        height: 80,
        backgroundColor: "#1e293b",
        border: "3px solid #3b82f6",
        borderRadius: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "16px",
        fontWeight: "bold",
        color: "white",
        boxShadow: "0 4px 20px rgba(59, 130, 246, 0.3)",
      }}
    >
      Kafka Cluster
    </div>
  );

  return (
    <div>
      {topicLabels}
      {messages}
      {kafkaCluster}
      <div
        style={{
          position: "absolute",
          left: centerX - 100,
          top: centerY - 180,
          fontSize: "18px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
        }}
      >
        Kafka Async Processing
      </div>
    </div>
  );
};

// Key points review component
const KeyPointsReview = ({
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

  // Section 4: 0.75-1.0
  const sectionProgress = Math.min(Math.max((progress - 0.75) / 0.25, 0), 1);

  const keyPoints = [
    {
      title: "Data Validation",
      points: [
        "Schema validation",
        "Budget verification",
        "Permission checks",
        "Data integrity",
      ],
    },
    {
      title: "State Management",
      points: [
        "DRAFT → PENDING",
        "PENDING → APPROVED",
        "APPROVED → COMPLETED",
        "Error handling",
      ],
    },
    {
      title: "Async Processing",
      points: [
        "Kafka messaging",
        "Event-driven architecture",
        "Scalable processing",
        "Reliable delivery",
      ],
    },
    {
      title: "System Benefits",
      points: [
        "Real-time validation",
        "Clear state transitions",
        "High throughput",
        "Fault tolerance",
      ],
    },
  ];

  // Show points based on progress
  const visiblePoints = Math.floor(sectionProgress * keyPoints.length);

  const pointCards = keyPoints
    .slice(0, visiblePoints + 1)
    .map((point, index) => {
      const x = centerX + (index % 2 === 0 ? -200 : 200);
      const y = centerY + (index < 2 ? -100 : 100);
      const cardOpacity =
        index === visiblePoints ? sectionProgress * 4 - index : 1;

      return (
        <div
          key={index}
          style={{
            position: "absolute",
            left: x - 120,
            top: y - 80,
            width: 240,
            backgroundColor: "#f8fafc",
            border: "2px solid #3b82f6",
            borderRadius: "12px",
            padding: "16px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            opacity: cardOpacity,
            transform: `scale(${0.8 + cardOpacity * 0.2})`,
            transition: "all 0.3s ease",
          }}
        >
          <div
            style={{
              fontSize: "16px",
              fontWeight: "bold",
              color: "#3b82f6",
              marginBottom: "8px",
              textAlign: "center",
            }}
          >
            {point.title}
          </div>
          <ul
            style={{
              fontSize: "12px",
              color: "#475569",
              paddingLeft: "20px",
              margin: "0",
            }}
          >
            {point.points.map((item, itemIndex) => (
              <li key={itemIndex} style={{ marginBottom: "4px" }}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      );
    });

  return (
    <div>
      {pointCards}
      <div
        style={{
          position: "absolute",
          left: centerX - 120,
          top: 50,
          fontSize: "24px",
          fontWeight: "bold",
          color: "#374151",
          textAlign: "center",
        }}
      >
        Key Points Review
      </div>
    </div>
  );
};

// Main enhanced flow component
export const ProjectApprovalFlowEnhanced: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Total duration: 450 frames (15 seconds at 30fps)
  const totalDuration = 450;
  const progress = Math.min(frame / totalDuration, 1);

  // Determine which section to show
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
      {/* Background gradient */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
        }}
      />

      {/* Section title */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: "28px",
          fontWeight: "bold",
          color: "white",
          textShadow: "0 2px 8px rgba(0,0,0,0.5)",
        }}
      >
        Project Approval Flow - Enhanced
      </div>

      {/* Progress indicator */}
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

      {/* Section indicators */}
      {[1, 2, 3, 4].map((section) => {
        const sectionNames = [
          "Data Validation",
          "Status Flow",
          "Kafka Processing",
          "Key Review",
        ];
        const isActive = section === currentSection;
        const isCompleted = section < currentSection;

        return (
          <div
            key={section}
            style={{
              position: "absolute",
              bottom: 40,
              left: 100 + (section - 1) * 150,
              width: 120,
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

      {/* Render current section */}
      {currentSection === 1 && (
        <DataStructureValidation
          progress={progress}
          width={width}
          height={height}
        />
      )}
      {currentSection === 2 && (
        <StatusTransition progress={progress} width={width} height={height} />
      )}
      {currentSection === 3 && (
        <KafkaAsyncProcessing
          progress={progress}
          width={width}
          height={height}
        />
      )}
      {currentSection === 4 && (
        <KeyPointsReview progress={progress} width={width} height={height} />
      )}
    </div>
  );
};

// Schema for the composition
export const ProjectApprovalFlowEnhancedSchema = z.object({});
