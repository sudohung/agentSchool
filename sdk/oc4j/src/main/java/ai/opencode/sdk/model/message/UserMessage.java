package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.FileDiff;
import ai.opencode.sdk.model.common.ModelRef;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class UserMessage implements Message {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String role = "user";
    private TimeInfo time;
    private Map<String, Object> format;
    private SummaryInfo summary;
    private String agent;
    private ModelRef model;
    private String system;
    private Map<String, Boolean> tools;
    private String variant;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TimeInfo {
        private Long created;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class SummaryInfo {
        private String title;
        private String body;
        private List<FileDiff> diffs;
    }
}
