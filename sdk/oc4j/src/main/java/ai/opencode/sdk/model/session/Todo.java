package ai.opencode.sdk.model.session;

import lombok.Data;

/**
 * Todo item.
 */
@Data
public class Todo {
    private String id;
    private String content;
    private String status;
    private String priority;
    private Long createdAt;
}
