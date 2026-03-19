package ai.opencode.sdk.model.event;

import ai.opencode.sdk.model.question.QuestionRequest;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventQuestionAsked extends Event {
    private QuestionRequest properties;
}