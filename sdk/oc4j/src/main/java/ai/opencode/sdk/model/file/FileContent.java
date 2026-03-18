package ai.opencode.sdk.model.file;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class FileContent {
    private ContentType type;
    private String content;
    private String diff;
    private Object patch;
    private String encoding;
    
    @JsonProperty("mimeType")
    private String mimeType;

    public enum ContentType {
        @JsonProperty("text")
        TEXT,
        @JsonProperty("binary")
        BINARY
    }
}