import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bot.agent import root_agent


class AgentService:
    def __init__(self):
        self.session_service = InMemorySessionService()

        self.agent = root_agent
        self.runner = Runner(
            agent=self.agent,
            app_name="root_agent",
            session_service=self.session_service
        )


    async def process_request(self, user_id: str, session_id: str, message: str) -> str | None:
        """
        Sends a query to the agent and prints the final response.
        """
        logging.info("Processing request - user_id: %s, session_id: %s", user_id, session_id)

        # Ensure session exists
        try:
            await self.session_service.get_session(user_id=user_id, session_id=session_id)
        except Exception as e:
            logging.info("Creating new session for %s: %s", session_id, e)
            await self.session_service.create_session(
                app_name="root_agent",
                user_id=user_id,
                session_id=session_id
            )

        content = types.Content(role='user', parts=[types.Part(text=message)])
        final_response_text = "Agent did not produce a final response."

        # Iterate through all events. Do not 'break' early to allow 
        # the runner to clean up OpenTelemetry contexts naturally.
        async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
        ):
            logging.debug(
                "Event: Author=%s, Type=%s, Final=%s",
                event.author, type(event).__name__, event.is_final_response()
            )

            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"

        return final_response_text
