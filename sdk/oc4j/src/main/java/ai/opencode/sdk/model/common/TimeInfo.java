package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * Time information for sessions and messages.
 */
@Data
public class TimeInfo {
    @JsonProperty("created")
    private Long created;

    @JsonProperty("updated")
    private Long updated;

    @JsonProperty("compacting")
    private Long compacting;

    @JsonProperty("archived")
    private Long archived;
}
