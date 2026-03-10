"""Example: Listen to events."""

from opencode_4_py import OpenCodeClient


def main():
    with OpenCodeClient() as client:
        # Create a session first
        session = client.session.create(title="Event Demo")
        print(f"Created session: {session.id}")
        
        # Subscribe to global events
        print("\nListening for events...")
        
        count = 0
        for event in client.event.subscribe_global():
            print(f"Event: {event.type}")
            print(f"Directory: {event.directory}")
            
            count += 1
            if count >= 5:  # Exit after 5 events
                break


if __name__ == "__main__":
    main()
