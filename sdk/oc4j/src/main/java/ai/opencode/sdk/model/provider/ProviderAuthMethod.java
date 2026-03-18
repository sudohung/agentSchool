package ai.opencode.sdk.model.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ProviderAuthMethod {
    private AuthType type;
    private String label;

    public enum AuthType {
        @JsonProperty("oauth")
        OAUTH,
        @JsonProperty("api")
        API
    }
}