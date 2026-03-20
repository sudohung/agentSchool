package ai.opencode.sdk.model.event;

import ai.opencode.sdk.model.session.Todo;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.List;
import java.util.Objects;

@Data
@EqualsAndHashCode(callSuper = true)
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventTodoUpdated extends Event {
    private Properties properties;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Properties {
        @JsonProperty("sessionID")
        private String sessionId;
        
        private List<Todo> todos;
    }

}

