package ai.openclaw.ocjbot.harness.loop;

import ai.openclaw.ocjbot.harness.*;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.Map;

/**
 * ReAct Loop 实现
 * 
 * 实现 Reason + Act 循环：
 * 1. Thought: 思考当前状态和下一步
 * 2. Action: 选择并执行动作
 * 3. Observation: 观察执行结果
 * 4. 重复直到完成或达到最大迭代次数
 */
public class ReActLoop implements AgentLoop {
    
    private static final Logger log = LoggerFactory.getLogger(ReActLoop.class);
    
    private final Harness harness;
    private final int maxIterations;
    
    public ReActLoop(Harness harness) {
        this(harness, 10);
    }
    
    public ReActLoop(Harness harness, int maxIterations) {
        this.harness = harness;
        this.maxIterations = maxIterations;
    }
    
    @Override
    public LoopResult run(Goal goal, AgentContext context) {
        log.info("Starting ReAct Loop for goal: {}", goal.getDescription());
        
        context.setMaxIterations(maxIterations);
        context.setStartTime(Instant.now());
        
        while (!context.hasExceededMaxIterations()) {
            context.incrementIteration();
            
            log.debug("Iteration {}/{}", context.getIterationCount(), maxIterations);
            
            // 1. 护栏检查
            if (!checkGuardrails(context)) {
                return LoopResult.costExceeded();
            }
            
            // 2. 感知
            PerceptionInput perceptionInput = perceive(goal, context);
            
            // 3. 规划
            PlanResult planResult = plan(perceptionInput, goal, context);
            
            if (planResult.isFinished()) {
                log.info("Goal achieved after {} iterations", context.getIterationCount());
                return LoopResult.success(planResult.getOutput());
            }
            
            // 4. 行动
            if (planResult.hasAction()) {
                ActionResult actionResult = act(planResult, context);
                
                // 5. 观察
                observe(actionResult, context);
            }
        }
        
        log.warn("Max iterations exceeded: {}", maxIterations);
        return LoopResult.maxIterationsExceeded(context.getIterationCount());
    }
    
    @Override
    public int getMaxIterations() {
        return maxIterations;
    }
    
    @Override
    public String getName() {
        return "ReAct Loop";
    }
    
    private boolean checkGuardrails(AgentContext context) {
        return context.getIterationCount() < maxIterations;
    }
    
    private PerceptionInput perceive(Goal goal, AgentContext context) {
        log.debug("Perceiving: {}", goal.getDescription());
        
        return PerceptionInput.builder()
            .userMessage(goal.getDescription())
            .sessionId(context.getSessionId())
            .build();
    }
    
    private PlanResult plan(PerceptionInput input, Goal goal, AgentContext context) {
        log.debug("Planning for: {}", input.getUserMessage());
        
        try {
            AgentRuntime runtime = context.getRuntime();
            if (runtime == null) {
                runtime = harness.getRuntime();
            }
            
            MessageRequest request = MessageRequest.builder()
                .text(buildPrompt(input, goal, context))
                .build();
            
            RuntimeMessage response = runtime.sendText(context.getSessionId(), input.getUserMessage());
            
            String content = response.getTextContent();
            boolean finished = shouldFinish(content, goal);
            boolean hasAction = hasToolCall(content);
            
            return PlanResult.builder()
                .thought(extractThought(content))
                .output(content)
                .finished(finished)
                .hasAction(hasAction)
                .action(extractAction(content))
                .build();
            
        } catch (Exception e) {
            log.error("Planning failed", e);
            return PlanResult.builder()
                .finished(false)
                .output("Error: " + e.getMessage())
                .build();
        }
    }
    
    private ActionResult act(PlanResult plan, AgentContext context) {
        log.debug("Acting: {}", plan.getAction());
        
        return ActionResult.builder()
            .success(true)
            .output("Action executed: " + plan.getAction())
            .build();
    }
    
    private void observe(ActionResult actionResult, AgentContext context) {
        log.debug("Observing: {}", actionResult.getOutput());
        
        context.getState().put("lastObservation", actionResult.getOutput());
    }
    
    private String buildPrompt(PerceptionInput input, Goal goal, AgentContext context) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("You are an AI assistant. Your goal is: ").append(goal.getDescription()).append("\n\n");
        
        if (!context.getMessages().isEmpty()) {
            prompt.append("Conversation history:\n");
            for (RuntimeMessage msg : context.getMessages()) {
                prompt.append(msg.getRole()).append(": ").append(msg.getTextContent()).append("\n");
            }
            prompt.append("\n");
        }
        
        prompt.append("User: ").append(input.getUserMessage());
        
        return prompt.toString();
    }
    
    private boolean shouldFinish(String content, Goal goal) {
        if (content == null) return false;
        
        // 简单判断：如果回复包含完成标记，则认为完成
        return content.contains("[DONE]") || 
               content.contains("Task completed") ||
               content.length() > 50; // 对于聊天场景，回复超过一定长度就认为完成
    }
    
    private boolean hasToolCall(String content) {
        if (content == null) return false;
        return content.contains("tool_call") || content.contains("Action:");
    }
    
    private String extractThought(String content) {
        if (content == null) return "";
        return content;
    }
    
    private String extractAction(String content) {
        if (content == null) return "";
        if (content.contains("Action:")) {
            int idx = content.indexOf("Action:");
            return content.substring(idx).split("\n")[0];
        }
        return "";
    }
}