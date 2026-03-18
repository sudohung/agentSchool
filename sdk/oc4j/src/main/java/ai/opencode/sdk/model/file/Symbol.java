package ai.opencode.sdk.model.file;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Symbol {
    private String name;
    private Integer kind;
    private Object location;
}