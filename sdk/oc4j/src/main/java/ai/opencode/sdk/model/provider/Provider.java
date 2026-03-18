package ai.opencode.sdk.model.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Provider {
    private String id;
    private String name;
    private ProviderSource source;
    
    @JsonProperty("env")
    private List<String> env;
    
    private String key;
    private Map<String, Object> options;
    private Map<String, Object> models;
    private String api;
    private String npm;

    public enum ProviderSource {
        @JsonProperty("env")
        ENV,
        @JsonProperty("config")
        CONFIG,
        @JsonProperty("custom")
        CUSTOM,
        @JsonProperty("api")
        API
    }
}