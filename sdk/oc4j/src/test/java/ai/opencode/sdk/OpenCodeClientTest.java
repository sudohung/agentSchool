package ai.opencode.sdk;

import ai.opencode.sdk.model.session.Session;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.*;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class OpenCodeClientTest {
    private MockWebServer mockWebServer;
    private OpenCodeClient client;

    @BeforeEach
    void setUp() throws Exception {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        ClientConfig config = ClientConfig.builder()
            .baseUrl(mockWebServer.url("/").toString())
            .build();

        client = new OpenCodeClient(config);
    }

    @AfterEach
    void tearDown() throws Exception {
        client.close();
        mockWebServer.shutdown();
    }

    @Test
    void testHealthCheck() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setBody("{\"healthy\":true,\"version\":\"1.0.0\"}"));

        // Health check should work
        assertNotNull(client.getGlobal());
    }

    @Test
    void testListSessions() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setBody("[]"));

        List<Session> sessions = client.getSession().list();
        assertNotNull(sessions);
        assertTrue(sessions.isEmpty());
    }

    @Test
    void testClientConfigDefaults() {
        ClientConfig config = ClientConfig.builder().build();
        assertEquals("http://127.0.0.1:4096", config.getBaseUrl());
        assertNotNull(config.getTimeout());
    }

    @Test
    void testClientConfigWithPassword() {
        ClientConfig config = ClientConfig.builder()
            .password("test-pass")
            .build();
        assertEquals("opencode", config.getUsername());
        assertEquals("test-pass", config.getPassword());
    }
}
