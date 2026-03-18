package ai.opencode.sdk.model.file;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class TextSearchMatch {
    private String path;
    private Integer line;
    private Integer column;
    private String text;
}