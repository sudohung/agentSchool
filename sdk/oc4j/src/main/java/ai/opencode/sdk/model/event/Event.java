package ai.opencode.sdk.model.event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

/**
 * Base class for all SSE events.
 * Uses Jackson polymorphic deserialization based on "type" field.
 * 
 * @see EventTypes for all supported event type IDs
 * @see EventType for enum representation
 */
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.PROPERTY,
    property = "type"
)
@JsonSubTypes({
    // Session events
    @JsonSubTypes.Type(value = EventSessionCreated.class, name = EventTypes.SESSION_CREATED),
    @JsonSubTypes.Type(value = EventSessionUpdated.class, name = EventTypes.SESSION_UPDATED),
    @JsonSubTypes.Type(value = EventSessionDeleted.class, name = EventTypes.SESSION_DELETED),
    @JsonSubTypes.Type(value = EventSessionStatus.class, name = EventTypes.SESSION_STATUS),
    @JsonSubTypes.Type(value = EventSessionIdle.class, name = EventTypes.SESSION_IDLE),
    @JsonSubTypes.Type(value = EventSessionDiff.class, name = EventTypes.SESSION_DIFF),
    @JsonSubTypes.Type(value = EventSessionError.class, name = EventTypes.SESSION_ERROR),
    // Message events
    @JsonSubTypes.Type(value = EventMessageUpdated.class, name = EventTypes.MESSAGE_UPDATED),
    @JsonSubTypes.Type(value = EventMessageRemoved.class, name = EventTypes.MESSAGE_REMOVED),
    @JsonSubTypes.Type(value = EventMessagePartUpdated.class, name = EventTypes.MESSAGE_PART_UPDATED),
    @JsonSubTypes.Type(value = EventMessagePartDelta.class, name = EventTypes.MESSAGE_PART_DELTA),
    // Permission events
    @JsonSubTypes.Type(value = EventPermissionAsked.class, name = EventTypes.PERMISSION_ASKED),
    @JsonSubTypes.Type(value = EventPermissionReplied.class, name = EventTypes.PERMISSION_REPLIED),
    // Question events
    @JsonSubTypes.Type(value = EventQuestionAsked.class, name = EventTypes.QUESTION_ASKED),
    // Todo events
    @JsonSubTypes.Type(value = EventTodoUpdated.class, name = EventTypes.TODO_UPDATED),
    // File events
    @JsonSubTypes.Type(value = EventFileEdited.class, name = EventTypes.FILE_EDITED),
    @JsonSubTypes.Type(value = EventFileWatcherUpdated.class, name = EventTypes.FILE_WATCHER_UPDATED),
    // Server events
    @JsonSubTypes.Type(value = EventServerConnected.class, name = EventTypes.SERVER_CONNECTED),
    @JsonSubTypes.Type(value = EventServerHeartbeat.class, name = EventTypes.SERVER_HEARTBEAT),
    // Global events
    @JsonSubTypes.Type(value = EventGlobalDisposed.class, name = EventTypes.GLOBAL_DISPOSED)
})
@JsonIgnoreProperties(ignoreUnknown = true)
public abstract class Event {
    private String type;

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }
}