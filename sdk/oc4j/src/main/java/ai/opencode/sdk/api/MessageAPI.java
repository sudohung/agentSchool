package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.message.MessageWithParts;
import lombok.RequiredArgsConstructor;

import java.util.*;

/**
 * Message API for managing messages.
 */
@RequiredArgsConstructor
public class MessageAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List messages in a session.
     * @param sessionId session ID
     * @return list of messages with parts
     */
    public List<MessageWithParts> list(String sessionId) {
        return http.get("/session/" + sessionId + "/message", List.class);
    }

    /**
     * List messages in a session with limit.
     * @param sessionId session ID
     * @param limit max results
     * @return list of messages with parts
     */
    public List<MessageWithParts> list(String sessionId, Integer limit) {
        Map<String, Object> params = new HashMap<>();
        if (limit != null) params.put("limit", limit);
        if (directory != null) params.put("directory", directory);
        return http.get("/session/" + sessionId + "/message", params, List.class);
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

    /**
     * Send a text message.
     * @param sessionId session ID
     * @param text message text
     * @return response message with parts
     */
    public MessageWithParts sendText(String sessionId, String text) {
        return sendText(sessionId, text, null, null, null, false);
    }

    /**
     * Send a text message.
     * @param sessionId session ID
     * @param text message text
     * @param providerId provider ID
     * @param modelId model ID
     * @param agent agent name
     * @param noReply don't wait for reply
     * @return response message with parts
     */
    public MessageWithParts sendText(String sessionId, String text, String providerId, 
                                     String modelId, String agent, boolean noReply) {
        Map<String, Object> part = new HashMap<>();
        part.put("type", "text");
        part.put("text", text);
        
        return send(sessionId, Collections.singletonList(part), providerId, modelId, agent, null, noReply, null);
    }

    /**
     * Send a message.
     * @param sessionId session ID
     * @param parts message parts
     * @param providerId provider ID
     * @param modelId model ID
     * @param agent agent name
     * @param system system prompt
     * @param noReply don't wait for reply
     * @param format output format
     * @return response message with parts
     */
    public MessageWithParts send(String sessionId, List<Map<String, Object>> parts,
                                 String providerId, String modelId, String agent,
                                 String system, boolean noReply, Map<String, Object> format) {
        Map<String, Object> body = new HashMap<>();
        body.put("parts", parts);
        
        if (agent != null) body.put("agent", agent);
        if (providerId != null && modelId != null) {
            Map<String, String> model = new HashMap<>();
            model.put("providerID", providerId);
            model.put("modelID", modelId);
            body.put("model", model);
        }
        if (system != null) body.put("system", system);
        if (noReply) body.put("noReply", true);
        if (format != null) body.put("format", format);
        
        return http.post("/session/" + sessionId + "/message", body, MessageWithParts.class);
    }

    /**
     * Send a message asynchronously (no wait).
     * @param sessionId session ID
     * @param parts message parts
     * @param providerId provider ID
     * @param modelId model ID
     * @param agent agent name
     * @param system system prompt
     */
    public void sendAsync(String sessionId, List<Map<String, Object>> parts,
                          String providerId, String modelId, String agent, String system) {
        Map<String, Object> body = new HashMap<>();
        body.put("parts", parts);
        
        if (agent != null) body.put("agent", agent);
        if (providerId != null && modelId != null) {
            Map<String, String> model = new HashMap<>();
            model.put("providerID", providerId);
            model.put("modelID", modelId);
            body.put("model", model);
        }
        if (system != null) body.put("system", system);
        
        http.post("/session/" + sessionId + "/prompt_async", body, Void.class);
    }

    /**
     * Execute a slash command.
     * @param sessionId session ID
     * @param command command name
     * @param arguments command arguments
     * @param providerId provider ID
     * @param modelId model ID
     * @param agent agent name
     * @return response message with parts
     */
    public MessageWithParts command(String sessionId, String command, String arguments,
                                     String providerId, String modelId, String agent) {
        Map<String, Object> body = new HashMap<>();
        body.put("command", command);
        
        if (arguments != null) body.put("arguments", arguments);
        if (agent != null) body.put("agent", agent);
        if (providerId != null && modelId != null) {
            Map<String, String> model = new HashMap<>();
            model.put("providerID", providerId);
            model.put("modelID", modelId);
            body.put("model", model);
        }
        
        return http.post("/session/" + sessionId + "/command", body, MessageWithParts.class);
    }

    /**
     * Execute a slash command.
     * @param sessionId session ID
     * @param command command name
     * @return response message with parts
     */
    public MessageWithParts command(String sessionId, String command) {
        return command(sessionId, command, null, null, null, null);
    }

    /**
     * Run a shell command.
     * @param sessionId session ID
     * @param command shell command
     * @param providerId provider ID
     * @param modelId model ID
     * @param agent agent name (default: "build")
     * @return response message with parts
     */
    public MessageWithParts shell(String sessionId, String command, 
                                  String providerId, String modelId, String agent) {
        Map<String, Object> body = new HashMap<>();
        body.put("command", command);
        body.put("agent", agent != null ? agent : "build");
        
        if (providerId != null && modelId != null) {
            Map<String, String> model = new HashMap<>();
            model.put("providerID", providerId);
            model.put("modelID", modelId);
            body.put("model", model);
        }
        
        return http.post("/session/" + sessionId + "/shell", body, MessageWithParts.class);
    }

    /**
     * Run a shell command.
     * @param sessionId session ID
     * @param command shell command
     * @return response message with parts
     */
    public MessageWithParts shell(String sessionId, String command) {
        return shell(sessionId, command, null, null, null);
    }

    /**
     * Delete a message.
     * @param sessionId session ID
     * @param messageId message ID
     * @return true if deleted
     */
    public Boolean delete(String sessionId, String messageId) {
        return http.deleteWithResponse("/session/" + sessionId + "/message/" + messageId);
    }

    /**
     * Update a message part.
     * @param sessionId session ID
     * @param messageId message ID
     * @param partId part ID
     * @param updates part updates
     * @return true if successful
     */
    public Boolean updatePart(String sessionId, String messageId, String partId, Map<String, Object> updates) {
        return http.patch("/session/" + sessionId + "/message/" + messageId + "/part/" + partId, updates, Boolean.class);
    }

    /**
     * Delete a message part.
     * @param sessionId session ID
     * @param messageId message ID
     * @param partId part ID
     * @return true if deleted
     */
    public Boolean deletePart(String sessionId, String messageId, String partId) {
        return http.deleteWithResponse("/session/" + sessionId + "/message/" + messageId + "/part/" + partId);
    }
}