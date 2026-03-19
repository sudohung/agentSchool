package ai.opencode.sdk.model.question;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class QuestionInfo {
    private String question;
    private String header;
    private List<QuestionOption> options;
    private Boolean multiple;
    private Boolean custom;
}