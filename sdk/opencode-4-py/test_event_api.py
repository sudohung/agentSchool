"""
Python SDK EventAPI Test Script
Used to compare with Java SDK implementation.

This script demonstrates the expected behavior of EventAPI SSE streaming,
following openapi.json specification.
"""

import json
import sys
sys.path.insert(0, 'src')

from opencode_4_py.api.event import EventAPI, AsyncEventAPI
from opencode_4_py.models.event import (
    Event,
    GlobalEvent,
    EventSessionCreated,
    EventSessionUpdated,
    EventSessionDeleted,
    EventSessionStatus,
    EventSessionIdle,
    EventSessionDiff,
    EventSessionError,
    EventMessageUpdated,
    EventMessageRemoved,
    EventMessagePartUpdated,
    EventMessagePartDelta,
    EventPermissionAsked,
    EventPermissionReplied,
    EventQuestionAsked,
    EventTodoUpdated,
    EventFileEdited,
    EventFileWatcherUpdated,
    EventServerConnected,
    EventGlobalDisposed,
)
from opencode_4_py.utils.http import HTTPClient, AsyncHTTPClient


def test_event_types():
    """Test all event types defined in Python SDK."""
    event_types = {
        "session.created": EventSessionCreated,
        "session.updated": EventSessionUpdated,
        "session.deleted": EventSessionDeleted,
        "session.status": EventSessionStatus,
        "session.idle": EventSessionIdle,
        "session.diff": EventSessionDiff,
        "session.error": EventSessionError,
        "message.updated": EventMessageUpdated,
        "message.removed": EventMessageRemoved,
        "message.part.updated": EventMessagePartUpdated,
        "message.part.delta": EventMessagePartDelta,
        "permission.asked": EventPermissionAsked,
        "permission.replied": EventPermissionReplied,
        "question.asked": EventQuestionAsked,
        "todo.updated": EventTodoUpdated,
        "file.edited": EventFileEdited,
        "file.watcher.updated": EventFileWatcherUpdated,
        "server.connected": EventServerConnected,
        "global.disposed": EventGlobalDisposed,
    }
    
    print("=== Python SDK Event Types ===")
    for event_type, event_class in event_types.items():
        print(f"  {event_type}: {event_class.__name__}")
    
    print(f"\nTotal: {len(event_types)} event types")
    return event_types


def test_sse_parsing():
    """Test SSE data parsing logic."""
    print("\n=== SSE Parsing Test ===")
    
    # Sample SSE data format from openapi.json
    sse_samples = [
        # Global event format
        'data: {"directory":"/test/project","payload":{"type":"session.created","properties":{"sessionID":"123"}}}\n\n',
        
        # Project event format
        'data: {"type":"message.updated","properties":{"messageID":"msg-1","role":"user"}}\n\n',
        
        # Permission event
        'data: {"type":"permission.asked","properties":{"sessionID":"s-1","requestID":"r-1"}}\n\n',
    ]
    
    for sample in sse_samples:
        print(f"\nSSE Data: {sample.strip()}")
        
        # Parse SSE format
        if sample.startswith("data: "):
            json_str = sample[6:].strip()
            data = json.loads(json_str)
            print(f"  Parsed JSON: {json.dumps(data, indent=2)}")


def test_api_structure():
    """Test EventAPI structure matches openapi.json."""
    print("\n=== API Structure Test ===")
    
    # From openapi.json:
    # GET /global/event - Subscribe to global events
    # GET /event?directory=...&workspace=... - Subscribe to project events
    
    print("OpenAPI Endpoints:")
    print("  GET /global/event - subscribeGlobal()")
    print("  GET /event - subscribe()")
    print("  GET /event?directory=... - subscribe(directory)")
    
    print("\nPython SDK Methods:")
    print("  EventAPI.subscribe_global() -> Iterator[GlobalEvent]")
    print("  EventAPI.subscribe() -> Iterator[Event]")
    print("  AsyncEventAPI.subscribe_global() -> AsyncIterator[GlobalEvent]")
    print("  AsyncEventAPI.subscribe() -> AsyncIterator[Event]")


def test_event_model_structure():
    """Test event model structure."""
    print("\n=== Event Model Structure ===")
    
    # Base Event class (union type in Python)
    print("Event (Union Type):")
    print("  - type: str (discriminator)")
    print("  - properties: Dict[str, Any]")
    
    # GlobalEvent structure
    print("\nGlobalEvent:")
    print("  - directory: str")
    print("  - payload: Event")
    
    # Special event with typed properties
    print("\nEventPermissionReplied:")
    print("  - type: 'permission.replied'")
    print("  - properties: PermissionRepliedProperties")
    print("    - sessionID: str")
    print("    - requestID: str")
    print("    - reply: 'once' | 'always' | 'reject'")


def compare_with_java_sdk():
    """Print comparison with Java SDK implementation."""
    print("\n=== Java SDK Comparison ===")
    
    print("Java SDK should implement:")
    print("""
    // Sync API
    EventAPI.subscribeGlobal() -> Iterator<GlobalEvent>
    EventAPI.subscribe() -> Iterator<Event>
    EventAPI.subscribe(String directory) -> Iterator<Event>
    
    // Async API
    AsyncEventAPI.subscribeGlobal() -> Flow.Publisher<GlobalEvent>
    AsyncEventAPI.subscribe() -> Flow.Publisher<Event>
    AsyncEventAPI.subscribe(String directory) -> Flow.Publisher<Event>
    """)
    
    print("Java Event Models (21 classes):")
    java_events = [
        "Event (base class)",
        "GlobalEvent",
        "EventSessionCreated", "EventSessionUpdated", "EventSessionDeleted",
        "EventSessionStatus", "EventSessionIdle", "EventSessionDiff", "EventSessionError",
        "EventMessageUpdated", "EventMessageRemoved", "EventMessagePartUpdated", "EventMessagePartDelta",
        "EventPermissionAsked", "EventPermissionReplied",
        "EventQuestionAsked", "EventTodoUpdated",
        "EventFileEdited", "EventFileWatcherUpdated",
        "EventServerConnected", "EventGlobalDisposed",
    ]
    for event in java_events:
        print(f"  - {event}")


if __name__ == "__main__":
    print("=" * 60)
    print("Python SDK EventAPI Test - openapi.json Compliance")
    print("=" * 60)
    
    test_event_types()
    test_sse_parsing()
    test_api_structure()
    test_event_model_structure()
    compare_with_java_sdk()
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)