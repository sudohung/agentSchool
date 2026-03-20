package ai.opencode.sdk.model.message;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class MessageWithParts {
    private Map<String, Object> info;
    private List<Map<String, Object>> parts;
}
