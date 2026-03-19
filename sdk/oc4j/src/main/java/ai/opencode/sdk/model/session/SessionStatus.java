package ai.opencode.sdk.model.session;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.Data;

@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.PROPERTY,
    property = "type"
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = SessionStatus.Idle.class, name = "idle"),
    @JsonSubTypes.Type(value = SessionStatus.Retry.class, name = "retry"),
    @JsonSubTypes.Type(value = SessionStatus.Busy.class, name = "busy")
})
@JsonIgnoreProperties(ignoreUnknown = true)
public abstract class SessionStatus {

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Idle extends SessionStatus {
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Retry extends SessionStatus {
        private int attempt;
        private String message;
        private long next;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Busy extends SessionStatus {
    }
}