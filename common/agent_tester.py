

import asyncio
import os
from typing import List, Dict, Any
from google.genai import types
from google.adk.runners import LlmAgent, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.plugins.logging_plugin import LoggingPlugin

class MultiAgentTester:
    """Test harness for multi-agent email communication scenarios."""
    
    def __init__(self, agent: LlmAgent):
        """Initialize the test environment."""
        # Set up API key
        if not os.getenv('GOOGLE_API_KEY'):
            print('❌ GOOGLE_API_KEY environment variable not set.')
            raise ValueError('GOOGLE_API_KEY required')
        
        # Initialize services
        self.session_service = InMemorySessionService()
        self.artifacts_service = InMemoryArtifactService()
        self.memory_service = InMemoryMemoryService()
        
        self.runner = Runner(
            app_name='multi_agent_email_test',
            agent=agent,
            artifact_service=self.artifacts_service,
            session_service=self.session_service,
            memory_service=self.memory_service,
            plugins=[LoggingPlugin()]
        )
        
        self.session = None
    
    async def setup_session(self) -> None:
        """Create a new test session."""
        self.session = await self.session_service.create_session(
            state={}, 
            app_name='multi_agent_email_test', 
            user_id='test_user_123'
        )
        print(f"🔄 Created test session: {self.session.id}")
    
    async def send_message_and_collect_events(self, message: str) -> List[Any]:
        """Send a message and collect all events from the response."""
        print(f"\n👤 User: {message}")
        print("=" * 80)
        
        content = types.Content(role='user', parts=[types.Part(text=message)])
        events = self.runner.run_async(
            session_id=self.session.id, 
            user_id='test_user_123', 
            new_message=content
        )
        
        collected_events = []
        async for event in events:
            collected_events.append(event)
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"🤖 {event.author}: {part.text}")
                    elif hasattr(part, 'thought') and part.thought:
                        print(f"💭 {event.author} (thinking): {part.thought}")
        
        return collected_events


    
    
    async def run_agent(self, user_message: str):
        """Run a single test scenario."""
        await self.setup_session()
        events = await self.send_message_and_collect_events(user_message)
        print(events)
        return events
