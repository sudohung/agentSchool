package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Question API for managing questions.
 */
@RequiredArgsConstructor
public class QuestionAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List pending questions.
     * @return list of question requests
     */
    public List<Map<String, Object>> list() {
        return http.get("/question", List.class);
    }

    /**
     * Reply to a question.
     * @param requestId question request ID
     * @param answer selected answer(s)
     * @return true if successful
     */
    public Boolean reply(String requestId, List<String> answer) {
        Map<String, Object> body = new HashMap<>();
        body.put("answer", answer);
        return http.post("/question/" + requestId + "/reply", body, Boolean.class);
    }

    /**
     * Reject a question.
     * @param requestId question request ID
     * @param reason rejection reason
     * @return true if successful
     */
    public Boolean reject(String requestId, String reason) {
        Map<String, String> body = new HashMap<>();
        if (reason != null) body.put("reason", reason);
        return http.post("/question/" + requestId + "/reject", body, Boolean.class);
    }

    /**
     * Reject a question.
     * @param requestId question request ID
     * @return true if successful
     */
    public Boolean reject(String requestId) {
        return reject(requestId, null);
    }
}