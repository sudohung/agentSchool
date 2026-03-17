package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * Time information for message parts.
 */
@Data
public class PartTimeInfo {
    @JsonProperty("start")
    private Long start;

    @JsonProperty("end")
    private Long end;

    @JsonProperty("created")
    private Long created;

    @JsonProperty("compacted")
    private Long compacted;
}
