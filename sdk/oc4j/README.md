# OpenCode Java SDK (oc4j)

Java SDK for OpenCode Server.

## Installation

Add to your Maven pom.xml:

```xml
<dependency>
    <groupId>ai.opencode</groupId>
    <artifactId>oc4j</artifactId>
    <version>0.1.0</version>
</dependency>
```

## Quick Start

### Synchronous Client

```java
import ai.opencode.sdk.*;
import ai.opencode.sdk.model.session.Session;

import java.util.List;

try (OpenCodeClient client = new OpenCodeClient()) {
    // Health check
    var health = client.getGlobal().health();
    System.out.println("Healthy: " + health.get("healthy"));
    
    // List sessions
    List<Session> sessions = client.getSession().list();
    System.out.println("Found " + sessions.size() + " sessions");
    
    // List permissions
    var permissions = client.getPermission().list();
    for (var p : permissions) {
        System.out.println("Permission: " + p.getPermission());
        client.getPermission().reply(p.getId(), "once", null);
    }
}
```

### Asynchronous Client

```java
import ai.opencode.sdk.*;

import java.util.concurrent.CompletableFuture;

try (AsyncOpenCodeClient client = new AsyncOpenCodeClient()) {
    CompletableFuture<List<Session>> sessions = 
        client.getSession().list();
    
    sessions.thenApply(list -> {
        System.out.println("Found " + list.size() + " sessions");
        return list;
    }).join();
}
```

## Configuration

```java
import ai.opencode.sdk.*;

import java.time.Duration;

ClientConfig config = ClientConfig.builder()
    .baseUrl("http://127.0.0.1:4096")
    .username("opencode")
    .password("your-password")
    .timeout(Duration.ofSeconds(60))
    .directory("/path/to/project")
    .build();

OpenCodeClient client = new OpenCodeClient(config);
```

## API Reference

### Session API
- `list()` - List all sessions
- `get(id)` - Get session by ID
- `create(title, directory)` - Create new session
- `delete(id)` - Delete session
- `todos(id)` - Get session todos
- `status(id)` - Get session status

### Permission API
- `list()` - List pending permissions
- `reply(id, reply, message)` - Reply to permission request (once/always/reject)
- `respond(sessionId, permissionId, response)` - Respond to permission (deprecated)

### Message API
- `list(sessionId)` - List messages for a session
- `get(sessionId, messageId)` - Get message by ID

### File API
- `list(path)` - List files
- `read(path)` - Read file content
- `status()` - Get file status

### Provider API
- `list()` - List providers
- `auth()` - Get provider auth info

### Project API
- `list()` - List projects
- `current()` - Get current project

### Config API
- `get()` - Get configuration

### Agent API
- `list()` - List agents

### Command API
- `list()` - List commands

### Global API
- `health()` - Get health status
- `config()` - Get global config
- `updateConfig(config)` - Update global config
- `dispose()` - Dispose instance

## Error Handling

The SDK throws the following exceptions:

- `OpenCodeException` - Base exception
- `ConnectionException` - Network/connection errors
- `AuthenticationException` - Authentication failures
- `NotFoundException` - Resource not found (404)
- `APIException` - API errors with status code and response body

```java
try {
    client.getSession().list();
} catch (APIException e) {
    System.err.println("API error: " + e.getStatusCode());
    System.err.println("Response: " + e.getResponseBody());
} catch (ConnectionException e) {
    System.err.println("Connection failed: " + e.getMessage());
}
```

## Directory/Workspace Support

All API methods support `directory` and `workspace` query parameters:

```java
ClientConfig config = ClientConfig.builder()
    .directory("/path/to/project")
    .workspace("my-workspace")
    .build();

OpenCodeClient client = new OpenCodeClient(config);
```

## License

MIT
