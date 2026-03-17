package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.Map;

/**
 * Token information.
 */
@Data
public class TokenInfo {
    private Integer total;
    private Integer input;
    private Integer output;
    private Integer reasoning;
    private Map<String, Integer> cache;
}
