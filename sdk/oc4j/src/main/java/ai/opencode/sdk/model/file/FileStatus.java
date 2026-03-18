package ai.opencode.sdk.model.file;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class FileStatus {
    private String path;
    private String status;
    private Boolean staged;
    private Boolean modified;
    private Boolean deleted;
    private Boolean untracked;
}