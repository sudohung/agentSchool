package ai.opencode.sdk.model.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ProviderListResponse {
    @JsonProperty("all")
    private List<Map<String, Object>> all;
    
    private Map<String, String> default_;
    
    @JsonProperty("default")
    public void setDefault(Map<String, String> default_) {
        this.default_ = default_;
    }
    
    @JsonProperty("default")
    public Map<String, String> getDefault() {
        return default_;
    }
    
    private List<String> connected;
}