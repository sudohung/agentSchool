package ai.opencode.sdk.model.event;

/**
 * Event type ID constants for use in annotations and code.
 * These are compile-time constants required by Jackson's @JsonSubTypes annotation.
 */
public interface EventTypes {
    // Session events
    String SESSION_CREATED = "session.created";
    String SESSION_UPDATED = "session.updated";
    String SESSION_DELETED = "session.deleted";
    String SESSION_STATUS = "session.status";
    String SESSION_IDLE = "session.idle";
    String SESSION_DIFF = "session.diff";
    String SESSION_ERROR = "session.error";
    
    // Message events
    String MESSAGE_UPDATED = "message.updated";
    String MESSAGE_REMOVED = "message.removed";
    String MESSAGE_PART_UPDATED = "message.part.updated";
    String MESSAGE_PART_DELTA = "message.part.delta";
    
    // Permission events
    String PERMISSION_ASKED = "permission.asked";
    String PERMISSION_REPLIED = "permission.replied";
    
    // Question events
    String QUESTION_ASKED = "question.asked";
    
    // Todo events
    String TODO_UPDATED = "todo.updated";
    
    // File events
    String FILE_EDITED = "file.edited";
    String FILE_WATCHER_UPDATED = "file.watcher.updated";
    
    // Server events
    String SERVER_CONNECTED = "server.connected";
    String SERVER_HEARTBEAT = "server.heartbeat";
    
    // Global events
    String GLOBAL_DISPOSED = "global.disposed";
}
