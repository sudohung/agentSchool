package ai.openclaw.ocjbot;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.harness.Harness;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.model.RuntimeMessage;
import ai.openclaw.ocjbot.runtime.model.RuntimeSession;
import ai.openclaw.ocjbot.runtime.model.SessionCreateRequest;
import ai.openclaw.ocjbot.runtime.mock.MockRuntime;
import ai.openclaw.ocjbot.runtime.opencode.OpenCodeRuntime;
import ai.openclaw.ocjbot.runtime.opencode.OpenCodeRuntimeConfig;
import ai.opencode.sdk.tool.JsonUtil;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class OcjbotApplicationTest {

    @Autowired
    private Harness harness;

    @Autowired
    private AgentRuntime runtime;

    @Autowired
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
//        runtime = new MockRuntime();
        harness.getRuntime();
        runtime.initialize();
    }
    
    @Test
    void testApplicationExists() {
        assertNotNull(OcjbotApplication.class);
    }

    @Test
    void testRuntimeExists() throws JsonProcessingException {
        System.out.println("start result: " + objectMapper.writeValueAsString(runtime.listSessions()));
    }
    
    @Test
    void testPlanWithDefaultAgent() throws JsonProcessingException {
        // Create a session
//        SessionCreateRequest request = SessionCreateRequest.of("Test Plan Session");
//        RuntimeSession session = runtime.createSession(request);
//        assertNotNull(session);
//        System.out.println("start result: " + objectMapper.writeValueAsString(session));


        // Test plan method
        RuntimeMessage planResult = runtime.plan("ses_2dd37dce4ffeWU7dGNopKa2O2j", "设计一个crm系统，思考下整体架构设计；输出md文档到tmp目录");
//        RuntimeMessage planResult = runtime.sendText("ses_2dd37dce4ffeWU7dGNopKa2O2j", "design a crm system and give me a design docs");
        assertNotNull(planResult);
        System.out.println("Plan result: " + planResult.getTextContent());
    }
    
    @Test
    void testPlanWithSpecificAgent() {
        // Create a session
        SessionCreateRequest request = SessionCreateRequest.of("Test Plan with Agent Session");
        RuntimeSession session = runtime.createSession(request);
        assertNotNull(session);
        
        // Test planWithAgent method (MockRuntime specific)
        if (runtime instanceof MockRuntime) {
            MockRuntime mockRuntime = (MockRuntime) runtime;
            RuntimeMessage planResult = mockRuntime.planWithAgent(
                session.getId(), 
                "Build a mobile app", 
                "coder-agent"
            );
            assertNotNull(planResult);
            assertTrue(planResult.getTextContent().contains("coder-agent"));
            System.out.println("Plan with agent result: " + planResult.getTextContent());
        }
    }
}