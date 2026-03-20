package ai.openclaw.ocjbot.harness;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Agent 循环结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoopResult {
    
    private boolean success;
    private String output;
    private String error;
    private LoopStatus status;
    private int iterations;
    
    public enum LoopStatus {
        COMPLETED,
        MAX_ITERATIONS_EXCEEDED,
        COST_EXCEEDED,
        ERROR,
        CANCELLED
    }
    
    public static LoopResult success(String output) {
        return LoopResult.builder()
            .success(true)
            .output(output)
            .status(LoopStatus.COMPLETED)
            .build();
    }
    
    public static LoopResult maxIterationsExceeded(int iterations) {
        return LoopResult.builder()
            .success(false)
            .error("Max iterations exceeded")
            .status(LoopStatus.MAX_ITERATIONS_EXCEEDED)
            .iterations(iterations)
            .build();
    }
    
    public static LoopResult costExceeded() {
        return LoopResult.builder()
            .success(false)
            .error("Cost limit exceeded")
            .status(LoopStatus.COST_EXCEEDED)
            .build();
    }
    
    public static LoopResult error(String error) {
        return LoopResult.builder()
            .success(false)
            .error(error)
            .status(LoopStatus.ERROR)
            .build();
    }
}