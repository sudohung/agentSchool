package ai.opencode.sdk.api;

import ai.opencode.sdk.ClientConfig;
import ai.opencode.sdk.OpenCodeClient;
import ai.opencode.sdk.AsyncOpenCodeClient;
import ai.opencode.sdk.model.event.*;
import ai.opencode.sdk.http.SseIterator;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Flow;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Tests for EventAPI SSE streaming.
 * Strictly follows OpenAPI.json and Python SDK implementation.
 */
class EventAPITest {
    private MockWebServer mockWebServer;
    private OpenCodeClient syncClient;
    private AsyncOpenCodeClient asyncClient;

    @BeforeEach
    void setUp() throws Exception {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        String baseUrl = mockWebServer.url("/").toString();
        
        ClientConfig syncConfig = ClientConfig.builder()
            .baseUrl(baseUrl)
            .build();
        syncClient = new OpenCodeClient(syncConfig);

        ClientConfig asyncConfig = ClientConfig.builder()
            .baseUrl(baseUrl)
            .build();
        asyncClient = new AsyncOpenCodeClient(asyncConfig);
    }

    @AfterEach
    void tearDown() throws Exception {
        syncClient.close();
        asyncClient.close();
        mockWebServer.shutdown();
    }

    // ==================== Sync EventAPI Tests ====================

    @Test
    void testSubscribeGlobal_SseStream() throws Exception {
        // SSE response format: "data: {json}\n\n"
        String sseData = buildGlobalEventSse(
            "{\"directory\":\"/test/project\",\"payload\":{\"type\":\"session.created\",\"properties\":{\"sessionID\":\"session-123\"}}}"
        );
        
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(sseData));

        Iterator<GlobalEvent> iterator = syncClient.getEvent().subscribeGlobal();
        
        // Verify request
        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertEquals("GET", request.getMethod());
        assertTrue(request.getPath().contains("global/event"));

        // Verify event
        assertTrue(iterator.hasNext());
        GlobalEvent event = iterator.next();
        assertNotNull(event);
        assertEquals("/test/project", event.getDirectory());
        assertNotNull(event.getPayload());
        assertEquals("session.created", event.getPayload().getType());
    }

    @Test
    void testSubscribe_ProjectEvents() throws Exception {
        String sseData = buildEventSse(
            "{\"type\":\"session.updated\",\"properties\":{\"sessionID\":\"session-456\",\"status\":\"active\"}}",
            "{\"type\":\"message.updated\",\"properties\":{\"messageID\":\"msg-1\",\"role\":\"user\"}}"
        );
        
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(sseData));

        Iterator<Event> iterator = syncClient.getEvent().subscribe();
        
        // Verify request includes directory parameter
        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertEquals("GET", request.getMethod());
        assertTrue(request.getPath().contains("/event"));

        // Verify first event
        assertTrue(iterator.hasNext());
        Event event1 = iterator.next();
        assertNotNull(event1);
        assertEquals("session.updated", event1.getType());
        assertThat(event1).isInstanceOf(EventSessionUpdated.class);

        // Verify second event
        assertTrue(iterator.hasNext());
        Event event2 = iterator.next();
        assertNotNull(event2);
        assertEquals("message.updated", event2.getType());
        assertThat(event2).isInstanceOf(EventMessageUpdated.class);
    }

    @Test
    void testSubscribe_WithDirectory() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(""));

        syncClient.getEvent().subscribe("/custom/directory");
        
        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertTrue(request.getPath().contains("directory=%2Fcustom%2Fdirectory"));
    }

    @Test
    void testParseAllEventTypes() throws Exception {
        // Test all event types from Python SDK
        Object[][] eventTestCases = {
            {"session.created", EventSessionCreated.class},
            {"session.updated", EventSessionUpdated.class},
            {"session.deleted", EventSessionDeleted.class},
            {"session.status", EventSessionStatus.class},
            {"session.idle", EventSessionIdle.class},
            {"session.diff", EventSessionDiff.class},
            {"session.error", EventSessionError.class},
            {"message.updated", EventMessageUpdated.class},
            {"message.removed", EventMessageRemoved.class},
            {"message.part.updated", EventMessagePartUpdated.class},
            {"message.part.delta", EventMessagePartDelta.class},
            {"permission.asked", EventPermissionAsked.class},
            {"permission.replied", EventPermissionReplied.class},
            {"question.asked", EventQuestionAsked.class},
            {"todo.updated", EventTodoUpdated.class},
            {"file.edited", EventFileEdited.class},
            {"file.watcher.updated", EventFileWatcherUpdated.class},
            {"server.connected", EventServerConnected.class},
            {"global.disposed", EventGlobalDisposed.class}
        };

        for (Object[] testCase : eventTestCases) {
            String eventType = (String) testCase[0];
            Class<?> expectedClass = (Class<?>) testCase[1];

            String sseData = buildEventSse(
                String.format("{\"type\":\"%s\",\"properties\":{\"test\":\"data\"}}", eventType)
            );
            
            mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/event-stream")
                .setBody(sseData));

            Iterator<Event> iterator = syncClient.getEvent().subscribe();
            
            assertTrue(iterator.hasNext(), "Should have event for type: " + eventType);
            Event event = iterator.next();
            assertNotNull(event, "Event should not be null for type: " + eventType);
            assertEquals(eventType, event.getType(), "Event type should match: " + eventType);
            assertThat(event).isInstanceOf(expectedClass);
            
            // Consume the request for next iteration
            mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        }
    }

    @Test
    void testSseIterator_ClosesOnEnd() throws Exception {
        // Empty SSE stream
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(""));

        Iterator<Event> iterator = syncClient.getEvent().subscribe();
        assertFalse(iterator.hasNext());

        // Verify iterator is closed properly
        if (iterator instanceof SseIterator) {
            ((SseIterator<?>) iterator).close();
        }
    }

    // ==================== Async EventAPI Tests ====================

    @Test
    void testAsyncSubscribeGlobal() throws Exception {
        String sseData = buildGlobalEventSse(
            "{\"directory\":\"/async/test\",\"payload\":{\"type\":\"server.connected\",\"properties\":{}}}"
        );
        
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(sseData));

        CountDownLatch latch = new CountDownLatch(1);
        AtomicReference<GlobalEvent> receivedEvent = new AtomicReference<>();

        Flow.Publisher<GlobalEvent> publisher = asyncClient.getEvent().subscribeGlobal();
        publisher.subscribe(new Flow.Subscriber<GlobalEvent>() {
            private Flow.Subscription subscription;

            @Override
            public void onSubscribe(Flow.Subscription subscription) {
                this.subscription = subscription;
                subscription.request(1);
            }

            @Override
            public void onNext(GlobalEvent item) {
                receivedEvent.set(item);
                latch.countDown();
                subscription.cancel();
            }

            @Override
            public void onError(Throwable throwable) {
                fail("Should not error: " + throwable.getMessage());
            }

            @Override
            public void onComplete() {
            }
        });

        // Verify request
        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertEquals("GET", request.getMethod());
        assertTrue(request.getPath().contains("global/event"));

        // Wait for event
        assertTrue(latch.await(5, TimeUnit.SECONDS), "Should receive event within timeout");
        
        GlobalEvent event = receivedEvent.get();
        assertNotNull(event);
        assertEquals("/async/test", event.getDirectory());
        assertEquals("server.connected", event.getPayload().getType());
    }

    @Test
    void testAsyncSubscribe_ProjectEvents() throws Exception {
        String sseData = buildEventSse(
            "{\"type\":\"todo.updated\",\"properties\":{\"todos\":[]}}"
        );
        
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(sseData));

        CountDownLatch latch = new CountDownLatch(1);
        AtomicReference<Event> receivedEvent = new AtomicReference<>();

        Flow.Publisher<Event> publisher = asyncClient.getEvent().subscribe();
        publisher.subscribe(new Flow.Subscriber<Event>() {
            private Flow.Subscription subscription;

            @Override
            public void onSubscribe(Flow.Subscription subscription) {
                this.subscription = subscription;
                subscription.request(1);
            }

            @Override
            public void onNext(Event item) {
                receivedEvent.set(item);
                latch.countDown();
                subscription.cancel();
            }

            @Override
            public void onError(Throwable throwable) {
                fail("Should not error: " + throwable.getMessage());
            }

            @Override
            public void onComplete() {
            }
        });

        // Verify request
        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertEquals("GET", request.getMethod());
        assertTrue(request.getPath().contains("/event"));

        // Wait for event
        assertTrue(latch.await(5, TimeUnit.SECONDS), "Should receive event within timeout");
        
        Event event = receivedEvent.get();
        assertNotNull(event);
        assertEquals("todo.updated", event.getType());
        assertThat(event).isInstanceOf(EventTodoUpdated.class);
    }

    @Test
    void testAsyncSubscribe_WithDirectory() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(""));

        CountDownLatch latch = new CountDownLatch(1);

        Flow.Publisher<Event> publisher = asyncClient.getEvent().subscribe("/custom/async/dir");
        publisher.subscribe(new Flow.Subscriber<Event>() {
            @Override
            public void onSubscribe(Flow.Subscription subscription) {
                subscription.cancel();
                latch.countDown();
            }

            @Override
            public void onNext(Event item) {}

            @Override
            public void onError(Throwable throwable) {}

            @Override
            public void onComplete() {}
        });

        latch.await(2, TimeUnit.SECONDS);

        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull(request);
        assertTrue(request.getPath().contains("directory="));
    }

    @Test
    void testAsyncMultipleEvents() throws Exception {
        // Multiple events in one stream
        String sseData = buildEventSse(
            "{\"type\":\"session.created\",\"properties\":{}}",
            "{\"type\":\"message.updated\",\"properties\":{}}",
            "{\"type\":\"file.edited\",\"properties\":{}}"
        );
        
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setHeader("Content-Type", "text/event-stream")
            .setBody(sseData));

        List<Event> receivedEvents = new ArrayList<>();
        CountDownLatch latch = new CountDownLatch(3);

        Flow.Publisher<Event> publisher = asyncClient.getEvent().subscribe();
        publisher.subscribe(new Flow.Subscriber<Event>() {
            private Flow.Subscription subscription;

            @Override
            public void onSubscribe(Flow.Subscription subscription) {
                this.subscription = subscription;
                subscription.request(3);
            }

            @Override
            public void onNext(Event item) {
                receivedEvents.add(item);
                latch.countDown();
            }

            @Override
            public void onError(Throwable throwable) {
                fail("Should not error");
            }

            @Override
            public void onComplete() {
            }
        });

        // Wait for all events
        assertTrue(latch.await(5, TimeUnit.SECONDS), "Should receive 3 events");
        
        assertEquals(3, receivedEvents.size());
        assertEquals("session.created", receivedEvents.get(0).getType());
        assertEquals("message.updated", receivedEvents.get(1).getType());
        assertEquals("file.edited", receivedEvents.get(2).getType());
    }

    @Test
    void testErrorHandling() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(500)
            .setBody("Internal Server Error"));

        assertThrows(Exception.class, () -> {
            Iterator<Event> iterator = syncClient.getEvent().subscribe();
            iterator.hasNext();
        });
    }

    // ==================== Helper Methods ====================

    private String buildEventSse(String... events) {
        StringBuilder sb = new StringBuilder();
        for (String event : events) {
            sb.append("data: ").append(event).append("\n\n");
        }
        return sb.toString();
    }

    private String buildGlobalEventSse(String... events) {
        StringBuilder sb = new StringBuilder();
        for (String event : events) {
            sb.append("data: ").append(event).append("\n\n");
        }
        return sb.toString();
    }
}