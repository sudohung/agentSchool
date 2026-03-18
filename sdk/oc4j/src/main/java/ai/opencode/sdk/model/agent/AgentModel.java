package ai.opencode.sdk.model.agent;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AgentModel {
    @JsonProperty("providerID")
    private String providerId;
    
    @JsonProperty("modelID")
    private String modelId;
}