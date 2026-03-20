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
public class RuntimeProvider {
    
    private String id;
    private String name;
    private String type;
    private List<ModelInfo> models;
    private boolean authenticated;
    private Map<String, Object> config;
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ModelInfo {
        private String id;
        private String name;
        private String type;
        private int contextWindow;
        private Map<String, Object> capabilities;
    }
}