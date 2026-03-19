package ai.opencode.sdk.model.event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonValue;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventPermissionReplied extends Event {
    private PermissionRepliedProperties properties;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PermissionRepliedProperties {
        @JsonProperty("sessionID")
        private String sessionId;
        
        @JsonProperty("requestID")
        private String requestId;
        
        private PermissionReply reply;
    }

    public enum PermissionReply {
        ONCE("once"),
        ALWAYS("always"),
        REJECT("reject");

        private final String value;

        PermissionReply(String value) {
            this.value = value;
        }

        @JsonValue
        public String getValue() {
            return value;
        }
    }
}