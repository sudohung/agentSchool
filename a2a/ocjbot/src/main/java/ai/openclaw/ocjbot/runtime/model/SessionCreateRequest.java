package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SessionCreateRequest {
    
    private String title;
    private String parentId;
    private String workspaceId;
    private List<Map<String, Object>> permissions;
    private Map<String, Object> metadata;
    
    public static SessionCreateRequest of(String title) {
        return SessionCreateRequest.builder()
            .title(title)
            .build();
    }
}