package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * Model reference.
 */
@Data
public class ModelRef {
    @JsonProperty("providerID")
    private String providerId;

    @JsonProperty("modelID")
    private String modelId;
}
