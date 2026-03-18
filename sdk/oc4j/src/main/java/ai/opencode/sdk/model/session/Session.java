package ai.opencode.sdk.model.session;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.SessionSummary;
import ai.opencode.sdk.model.agent.AgentPermission;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;

@Data
public class Session {
    private String id;
    private String slug;
    
    @JsonProperty("projectID")
    private String projectId;
    
    @JsonProperty("workspaceID")
    private String workspaceId;
    
    private String directory;
    
    @JsonProperty("parentID")
    private String parentId;
    
    private SessionSummary summary;
    private ShareInfo share;
    private String title;
    private String version;
    private TimeInfo time;
    private List<AgentPermission> permission;
    private RevertInfo revert;
}
