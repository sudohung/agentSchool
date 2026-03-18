package ai.opencode.sdk.model.project;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Project {
    private String id;
    
    @JsonProperty("worktree")
    private String worktree;
    
    private String vcs;
    private String name;
    private Map<String, Object> icon;
    private Map<String, Object> commands;
    private Map<String, Object> time;
    
    @JsonProperty("sandboxes")
    private List<String> sandboxes;
}