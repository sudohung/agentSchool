package ai.openclaw.ocjbot.harness.loop;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 规划结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PlanResult {
    
    private String thought;
    private String action;
    private String output;
    private boolean finished;
    private boolean hasAction;
    
    public static PlanResult finished(String output) {
        return PlanResult.builder()
            .output(output)
            .finished(true)
            .hasAction(false)
            .build();
    }
    
    public static PlanResult action(String thought, String action) {
        return PlanResult.builder()
            .thought(thought)
            .action(action)
            .finished(false)
            .hasAction(true)
            .build();
    }
}