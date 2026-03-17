package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.message.MessageWithParts;
import lombok.RequiredArgsConstructor;

import java.util.List;

/**
 * Message API for managing messages.
 */
@RequiredArgsConstructor
public class MessageAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List messages for a session.
     * @param sessionId session ID
     * @return list of messages with parts
     */
    public List<MessageWithParts> list(String sessionId) {
        return http.get("/session/" + sessionId + "/message", List.class);
    }

    /**
     * Get message by ID.
     * @param sessionId session ID
     * @param messageId message ID
     * @return message with parts
     */
    public MessageWithParts get(String sessionId, String messageId) {
        return http.get("/session/" + sessionId + "/message/" + messageId, MessageWithParts.class);
    }
}
