package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.PartTimeInfo;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.Map;

/**
 * Text part.
 */
@Data
public class TextPart {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    @JsonProperty("messageID")
    private String messageId;
    
    private String type = "text";
    private String text;
    private Boolean synthetic;
    private Boolean ignored;
    private PartTimeInfo time;
    private Map<String, Object> metadata;
}
