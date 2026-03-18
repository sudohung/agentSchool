package ai.opencode.sdk;

import java.util.List;
import java.util.Map;

/**
 * Quick integration test to verify SDK connection.
 * Run: java -cp target/classes:target/test-classes:$(mvn dependency:build-classpath -q -Dmdep.outputFile=/dev/stdout) \
 *      ai.opencode.sdk.QuickIntegrationTest
 */
public class QuickIntegrationTest {
    
    public static void main(String[] args) {
        System.out.println("==========================================");
        System.out.println("Java OpenCode SDK Quick Integration Test");
        System.out.println("==========================================\n");
        
        String baseUrl = "http://127.0.0.1:4096";
        System.out.println("Connecting to: " + baseUrl);
        
        try {
            ClientConfig config = ClientConfig.builder()
                .baseUrl(baseUrl)
                .timeout(java.time.Duration.ofSeconds(10))
                .build();
            
            OpenCodeClient client = new OpenCodeClient(config);
            
            // Test 1: Health Check
            System.out.println("\n[1/10] Testing Global Health...");
            try {
                Map<String, Object> health = client.getGlobal().health();
                System.out.println("  ✓ Health check passed");
                System.out.println("    Response: " + health);
            } catch (Exception e) {
                System.out.println("  ✗ Health check failed: " + e.getMessage());
            }
            
            // Test 2: List Sessions
            System.out.println("\n[2/10] Testing Session List...");
            try {
                List<ai.opencode.sdk.model.session.Session> sessions = client.getSession().list();
                System.out.println("  ✓ Session list passed");
                System.out.println("    Found " + sessions.size() + " sessions");
            } catch (Exception e) {
                System.out.println("  ✗ Session list failed: " + e.getMessage());
            }
            
            // Test 3: List Files
            System.out.println("\n[3/10] Testing File List...");
            try {
                List<ai.opencode.sdk.model.file.FileNode> files = client.getFile().list();
                System.out.println("  ✓ File list passed");
                System.out.println("    Found " + files.size() + " files/directories");
            } catch (Exception e) {
                System.out.println("  ✗ File list failed: " + e.getMessage());
            }
            
            // Test 4: List Projects
            System.out.println("\n[4/10] Testing Project List...");
            try {
                List<ai.opencode.sdk.model.project.Project> projects = client.getProject().list();
                System.out.println("  ✓ Project list passed");
                System.out.println("    Found " + projects.size() + " projects");
            } catch (Exception e) {
                System.out.println("  ✗ Project list failed: " + e.getMessage());
            }
            
            // Test 5: Current Project
            System.out.println("\n[5/10] Testing Current Project...");
            try {
                ai.opencode.sdk.model.project.Project project = client.getProject().current();
                System.out.println("  ✓ Current project passed");
                System.out.println("    Project: " + project.getName());
            } catch (Exception e) {
                System.out.println("  ✗ Current project failed: " + e.getMessage());
            }
            
            // Test 6: List Agents
            System.out.println("\n[6/10] Testing Agent List...");
            try {
                List<ai.opencode.sdk.model.agent.Agent> agents = client.getAgent().list();
                System.out.println("  ✓ Agent list passed");
                System.out.println("    Found " + agents.size() + " agents");
                for (ai.opencode.sdk.model.agent.Agent agent : agents) {
                    System.out.println("      - " + agent.getName() + " [" + agent.getMode() + "]");
                }
            } catch (Exception e) {
                System.out.println("  ✗ Agent list failed: " + e.getMessage());
            }
            
            // Test 7: List Providers
            System.out.println("\n[7/10] Testing Provider List...");
            try {
                ai.opencode.sdk.model.provider.ProviderListResponse response = client.getProvider().list();
                System.out.println("  ✓ Provider list passed");
                System.out.println("    All: " + response.getAll().size());
                System.out.println("    Connected: " + response.getConnected().size());
            } catch (Exception e) {
                System.out.println("  ✗ Provider list failed: " + e.getMessage());
            }
            
            // Test 8: Get Config
            System.out.println("\n[8/10] Testing Config Get...");
            try {
                Map<String, Object> configMap = client.getConfig().get();
                System.out.println("  ✓ Config get passed");
                System.out.println("    Keys: " + configMap.keySet().size());
            } catch (Exception e) {
                System.out.println("  ✗ Config get failed: " + e.getMessage());
            }
            
            // Test 9: List Permissions
            System.out.println("\n[9/10] Testing Permission List...");
            try {
                List<ai.opencode.sdk.model.permission.PermissionRequest> permissions = client.getPermission().list();
                System.out.println("  ✓ Permission list passed");
                System.out.println("    Pending: " + permissions.size());
            } catch (Exception e) {
                System.out.println("  ✗ Permission list failed: " + e.getMessage());
            }
            
            // Test 10: LSP Status
            System.out.println("\n[10/10] Testing LSP Status...");
            try {
                List<Map<String, Object>> lspStatus = client.getLsp().status();
                System.out.println("  ✓ LSP status passed");
                System.out.println("    Servers: " + lspStatus.size());
            } catch (Exception e) {
                System.out.println("  ✗ LSP status failed: " + e.getMessage());
            }
            
            client.close();
            
            System.out.println("\n==========================================");
            System.out.println("Integration Test Completed!");
            System.out.println("==========================================\n");
            
        } catch (Exception e) {
            System.err.println("Failed to connect to server: " + e.getMessage());
            System.err.println("Please ensure the OpenCode server is running at " + baseUrl);
            e.printStackTrace();
            System.exit(1);
        }
    }
}
