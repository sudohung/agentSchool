package ai.opencode.sdk.api;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import ai.opencode.sdk.model.event.*;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for Event model parsing.
 * Tests Jackson deserialization of all event types.
 */
class EventModelTest {
    private ObjectMapper mapper;

    @BeforeEach
    void setUp() {
        mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        mapper.activateDefaultTyping(
            mapper.getPolymorphicTypeValidator(),
            ObjectMapper.DefaultTyping.NON_FINAL,
            JsonTypeInfo.As.PROPERTY
        );
    }

    @Test
    void testParseEventSessionCreated() throws Exception {
        String json = "{\"type\":\"session.created\",\"properties\":{\"sessionID\":\"s-123\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventSessionCreated.class);
        assertThat(event.getType()).isEqualTo("session.created");
        
        EventSessionCreated created = (EventSessionCreated) event;
    }

    @Test
    void testParseEventSessionUpdated() throws Exception {
        String json = "{\"type\":\"session.updated\",\"properties\":{\"sessionID\":\"s-456\",\"status\":\"active\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventSessionUpdated.class);
        assertThat(event.getType()).isEqualTo("session.updated");
    }

    @Test
    void testParseEventMessageUpdated() throws Exception {
        String json = "{\"type\":\"message.updated\",\"properties\":{\"messageID\":\"m-1\",\"role\":\"user\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventMessageUpdated.class);
        assertThat(event.getType()).isEqualTo("message.updated");
    }

    @Test
    void testParseEventMessagePartDelta() throws Exception {
        String json = "{\"type\":\"message.part.delta\",\"properties\":{\"partID\":\"p-1\",\"delta\":\"hello\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventMessagePartDelta.class);
        assertThat(event.getType()).isEqualTo("message.part.delta");
    }

    @Test
    void testParseEventPermissionAsked() throws Exception {
        String json = "{\"type\":\"permission.asked\",\"properties\":{\"sessionID\":\"s-1\",\"requestID\":\"r-1\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventPermissionAsked.class);
        assertThat(event.getType()).isEqualTo("permission.asked");
    }

    @Test
    void testParseEventPermissionReplied() throws Exception {
        String json = "{\"type\":\"permission.replied\",\"properties\":{\"sessionID\":\"s-1\",\"requestID\":\"r-1\",\"reply\":\"once\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventPermissionReplied.class);
        assertThat(event.getType()).isEqualTo("permission.replied");
        
        EventPermissionReplied replied = (EventPermissionReplied) event;
        assertThat(replied.getProperties()).isNotNull();
        assertThat(replied.getProperties().getSessionId()).isEqualTo("s-1");
        assertThat(replied.getProperties().getRequestId()).isEqualTo("r-1");
        assertThat(replied.getProperties().getReply()).isEqualTo("once");
    }

    @Test
    void testParseEventTodoUpdated() throws Exception {
        String json = "{\"type\":\"todo.updated\",\"properties\":{\"todos\":[]}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventTodoUpdated.class);
        assertThat(event.getType()).isEqualTo("todo.updated");
    }

    @Test
    void testParseEventFileEdited() throws Exception {
        String json = "{\"type\":\"file.edited\",\"properties\":{\"path\":\"/src/main.java\"}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventFileEdited.class);
        assertThat(event.getType()).isEqualTo("file.edited");
    }

    @Test
    void testParseEventServerConnected() throws Exception {
        String json = "{\"type\":\"server.connected\",\"properties\":{}}";
        Event event = mapper.readValue(json, Event.class);
        
        assertThat(event).isInstanceOf(EventServerConnected.class);
        assertThat(event.getType()).isEqualTo("server.connected");
    }

    @Test
    void testParseGlobalEvent() throws Exception {
        String json = "{\"directory\":\"/test/project\",\"payload\":{\"type\":\"session.created\",\"properties\":{\"sessionID\":\"s-123\"}}}";
        GlobalEvent event = mapper.readValue(json, GlobalEvent.class);
        
        assertThat(event.getDirectory()).isEqualTo("/test/project");
        assertThat(event.getPayload()).isNotNull();
        assertThat(event.getPayload().getType()).isEqualTo("session.created");
    }

    @Test
    void testAllEventTypes() throws Exception {
        String[][] eventTypes = {
            {"session.created", "EventSessionCreated"},
            {"session.updated", "EventSessionUpdated"},
            {"session.deleted", "EventSessionDeleted"},
            {"session.status", "EventSessionStatus"},
            {"session.idle", "EventSessionIdle"},
            {"session.diff", "EventSessionDiff"},
            {"session.error", "EventSessionError"},
            {"message.updated", "EventMessageUpdated"},
            {"message.removed", "EventMessageRemoved"},
            {"message.part.updated", "EventMessagePartUpdated"},
            {"message.part.delta", "EventMessagePartDelta"},
            {"permission.asked", "EventPermissionAsked"},
            {"permission.replied", "EventPermissionReplied"},
            {"question.asked", "EventQuestionAsked"},
            {"todo.updated", "EventTodoUpdated"},
            {"file.edited", "EventFileEdited"},
            {"file.watcher.updated", "EventFileWatcherUpdated"},
            {"server.connected", "EventServerConnected"},
            {"global.disposed", "EventGlobalDisposed"},
        };

        for (String[] type : eventTypes) {
            String json = String.format("{\"type\":\"%s\",\"properties\":{}}", type[0]);
            Event event = mapper.readValue(json, Event.class);
            
            assertThat(event.getType()).isEqualTo(type[0]);
            assertThat(event.getClass().getSimpleName()).isEqualTo(type[1]);
        }
    }
}