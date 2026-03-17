package ai.opencode.sdk.model.message;

import lombok.Data;
import java.util.List;

/**
 * Message with parts.
 */
@Data
public class MessageWithParts {
    private Object info;
    private List<Object> parts;
}
