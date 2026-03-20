package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.runtime.model.*;

/**
 * Agent Loop 接口
 * 
 * Agent 的核心推理循环，实现感知→规划→行动→记忆的闭环
 */
public interface AgentLoop {
    
    /**
     * 执行 Agent 循环
     * 
     * @param goal Agent 目标
     * @param context Agent 上下文
     * @return 循环结果
     */
    LoopResult run(Goal goal, AgentContext context);
    
    /**
     * 获取最大迭代次数
     */
    int getMaxIterations();
    
    /**
     * 获取循环名称
     */
    String getName();
}