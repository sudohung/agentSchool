package ai.opencode.sdk.model.event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.PROPERTY,
    property = "type"
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = EventSessionCreated.class, name = "session.created"),
    @JsonSubTypes.Type(value = EventSessionUpdated.class, name = "session.updated"),
    @JsonSubTypes.Type(value = EventSessionDeleted.class, name = "session.deleted"),
    @JsonSubTypes.Type(value = EventSessionStatus.class, name = "session.status"),
    @JsonSubTypes.Type(value = EventSessionIdle.class, name = "session.idle"),
    @JsonSubTypes.Type(value = EventSessionDiff.class, name = "session.diff"),
    @JsonSubTypes.Type(value = EventSessionError.class, name = "session.error"),
    @JsonSubTypes.Type(value = EventMessageUpdated.class, name = "message.updated"),
    @JsonSubTypes.Type(value = EventMessageRemoved.class, name = "message.removed"),
    @JsonSubTypes.Type(value = EventMessagePartUpdated.class, name = "message.part.updated"),
    @JsonSubTypes.Type(value = EventMessagePartDelta.class, name = "message.part.delta"),
    @JsonSubTypes.Type(value = EventPermissionAsked.class, name = "permission.asked"),
    @JsonSubTypes.Type(value = EventPermissionReplied.class, name = "permission.replied"),
    @JsonSubTypes.Type(value = EventQuestionAsked.class, name = "question.asked"),
    @JsonSubTypes.Type(value = EventTodoUpdated.class, name = "todo.updated"),
    @JsonSubTypes.Type(value = EventFileEdited.class, name = "file.edited"),
    @JsonSubTypes.Type(value = EventFileWatcherUpdated.class, name = "file.watcher.updated"),
    @JsonSubTypes.Type(value = EventServerConnected.class, name = "server.connected"),
    @JsonSubTypes.Type(value = EventGlobalDisposed.class, name = "global.disposed")
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