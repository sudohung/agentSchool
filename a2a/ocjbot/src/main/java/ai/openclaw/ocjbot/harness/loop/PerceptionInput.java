package ai.openclaw.ocjbot.harness.loop;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 感知输入
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PerceptionInput {
    
    private String sessionId;
    private String userMessage;
    private String systemPrompt;
    private String context;
}