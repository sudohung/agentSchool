package ai.opencode.sdk.model.project;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ProjectIcon {
    private String url;
    private String override;
    private String color;
}