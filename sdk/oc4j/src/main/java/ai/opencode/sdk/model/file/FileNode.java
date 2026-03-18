package ai.opencode.sdk.model.file;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class FileNode {
    private String name;
    private String path;
    private String absolute;
    private FileType type;
    private Boolean ignored;

    public enum FileType {
        @JsonProperty("file")
        FILE,
        @JsonProperty("directory")
        DIRECTORY
    }
}