package ai.opencode.sdk.model.project;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ProjectTime {
    private Long created;
    private Long updated;
    private Long initialized;
}