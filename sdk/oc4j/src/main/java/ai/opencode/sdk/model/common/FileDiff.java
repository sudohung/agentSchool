package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * File diff.
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class FileDiff {
    private String file;
    private String before;
    private String after;
    private int additions;
    private int deletions;
    private FileDiffStatus status;

    public enum FileDiffStatus {
        @JsonProperty("added")
        ADDED,
        @JsonProperty("deleted")
        DELETED,
        @JsonProperty("modified")
        MODIFIED
    }
}
