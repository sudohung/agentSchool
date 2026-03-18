package ai.opencode.sdk.model.session;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class RevertInfo {
    @JsonProperty("messageID")
    private String messageId;
    
    @JsonProperty("partID")
    private String partId;
    
    private String snapshot;
    private String diff;
}