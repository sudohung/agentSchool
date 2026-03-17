package ai.opencode.sdk.model.session;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.SessionSummary;
import ai.opencode.sdk.model.common.ModelRef;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * Session information.
 */
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
    private Map<String, String> share;
    private String title;
    private String version;
    private TimeInfo time;
    private Map<String, Object> permission;
    private Map<String, Object> revert;
}
