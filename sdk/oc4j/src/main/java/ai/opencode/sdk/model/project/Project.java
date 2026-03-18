package ai.opencode.sdk.model.project;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Project {
    private String id;
    
    @JsonProperty("worktree")
    private String worktree;
    
    @JsonProperty("vcs")
    private VcsType vcs;
    
    private String name;
    private ProjectIcon icon;
    private ProjectCommands commands;
    private ProjectTime time;
    
    @JsonProperty("sandboxes")
    private List<String> sandboxes;

    public enum VcsType {
        @JsonProperty("git")
        GIT
    }
}