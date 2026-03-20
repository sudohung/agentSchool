package ai.openclaw.ocjbot.harness.loop;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 行动结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ActionResult {
    
    private boolean success;
    private String output;
    private String error;
    
    public static ActionResult success(String output) {
        return ActionResult.builder()
            .success(true)
            .output(output)
            .build();
    }
    
    public static ActionResult failure(String error) {
        return ActionResult.builder()
            .success(false)
            .error(error)
            .build();
    }
}