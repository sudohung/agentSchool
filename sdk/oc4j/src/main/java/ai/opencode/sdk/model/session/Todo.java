package ai.opencode.sdk.model.session;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Todo {
    private String content;
    private TodoStatus status;
    private TodoPriority priority;

    public enum TodoStatus {
        @JsonProperty("pending")
        PENDING,
        @JsonProperty("in_progress")
        IN_PROGRESS,
        @JsonProperty("completed")
        COMPLETED,
        @JsonProperty("cancelled")
        CANCELLED
    }

    public enum TodoPriority {
        @JsonProperty("high")
        HIGH,
        @JsonProperty("medium")
        MEDIUM,
        @JsonProperty("low")
        LOW
    }
}
