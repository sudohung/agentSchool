package ai.opencode.sdk.model.question;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class QuestionOption {
    private String label;
    private String description;
}