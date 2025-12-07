from __future__ import annotations

import time
from typing import Optional, TYPE_CHECKING

from ..config import DustConfig
from ..exceptions import DustError
from ..conversations.models import (
    Message,
    MessageContext,
    MessageMention,
    MessageMentionContext,
    ConversationEventType,
)
from .models import ChatMessage, ChatResponse
from .exceptions import ChatError

if TYPE_CHECKING:
    from ..conversations.client import ConversationsClient
    from ..agents.client import AgentsClient


class ChatSession:
    """
    Stateful chat session bound to a given conversation, agent, and user identity.

    Use ChatClient.session(...) to create instances of this.
    """

    def __init__(
        self,
        *,
        chat_client: ChatClient,
        conversation_id: str,
        agent: str,
        username: str,
        timezone: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        self._chat_client = chat_client
        self._conversation_id = conversation_id
        self._agent = agent
        self._username = username
        self._timezone = timezone
        self._title = title

    # Read-only properties for introspection
    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    @property
    def agent(self) -> str:
        return self._agent

    @property
    def username(self) -> str:
        return self._username

    @property
    def timezone(self) -> Optional[str]:
        return self._timezone

    @property
    def title(self) -> Optional[str]:
        return self._title

    def send(self, text: str) -> ChatResponse:
        """
        Send a message within this session's conversation using the bound agent.

        This is blocking: it waits for the assistant reply using the events stream.
        """
        return self._chat_client._send_internal(
            agent=self._agent,
            text=text,
            username=self._username,
            timezone=self._timezone,
            conversation_id=self._conversation_id,
            title=self._title,
        )


class ChatClient:
    """
    High-level chat interface on top of Conversations & Agents.

    This client hides most of the low-level plumbing (MessageContext, mentions)
    and offers a simple API:

        - one-shot calls via `send(...)`
        - stateful sessions via `session(...)`

    It uses the Conversations *conversation events* stream under the hood to
    aggregate the assistant's reply in a blocking fashion (no streaming API
    surface yet).
    """

    def __init__(
        self,
        *,
        conversations: ConversationsClient,
        agents: AgentsClient,
        config: DustConfig,
    ) -> None:
        self._conversations = conversations
        self._agents = agents
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(
        self,
        *,
        agent: str,
        text: str,
        username: str,
        timezone: Optional[str] = None,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ChatResponse:
        """
        One-shot chat call.

        - If `conversation_id` is None, this creates a new conversation.
        - Otherwise, it sends the message in the existing conversation.
        - It then streams conversation events and aggregates the assistant reply.

        Args:
            agent: Agent configuration sId (e.g. "dust", "helper", "i5cIwRsG0u").
            text: User message content.
            username: Logical username for this user (required by Dust in most workspaces).
            timezone: Optional timezone.
            conversation_id: Optional existing conversation sId.
            title: Optional conversation title (only used when creating a new conversation).
            timeout: Optional override for how long to wait for events.
                     Defaults to `config.timeout` if not provided.

        Returns:
            ChatResponse with both the user message and (if available)
            the assistant reply.

        Raises:
            DustError / DustAPIError / ChatError on failures.
        """
        return self._send_internal(
            agent=agent,
            text=text,
            username=username,
            timezone=timezone,
            conversation_id=conversation_id,
            title=title,
            timeout=timeout or self._config.timeout,
        )

    def session(
        self,
        *,
        agent: str,
        username: str,
        timezone: Optional[str] = None,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ChatSession:
        """
        Create a stateful chat session bound to one agent and a conversation.

        If `conversation_id` is not provided, a new conversation is created.

        Example:
            session = client.chat.session(
                agent="dust",
                username="leo",
                timezone="Europe/Paris",
            )
            resp = session.send("Hello!")
        """
        # Ensure we have a conversation
        conv_id = conversation_id
        if conv_id is None:
            conv = self._conversations.create(title=title)
            conv_id = conv.sId

        return ChatSession(
            chat_client=self,
            conversation_id=conv_id,
            agent=agent,
            username=username,
            timezone=timezone,
            title=title,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_internal(
        self,
        *,
        agent: str,
        text: str,
        username: str,
        timezone: Optional[str],
        conversation_id: Optional[str],
        title: Optional[str],
        timeout: float,
    ) -> ChatResponse:
        """
        Core implementation used by both ChatClient.send and ChatSession.send.

        It:
          - ensures we have a conversationId
          - builds MessageContext + MessageMention
          - calls ConversationsClient.create_message
          - streams conversation events to build the assistant reply
          - wraps everything into ChatResponse
        """
        # 1) Ensure conversation exists
        conv_id = conversation_id
        if conv_id is None:
            conv = self._conversations.create(title=title)
            conv_id = conv.sId

        if not username:
            # Being strict here is better UX than letting the server 400 it.
            raise DustError(
                "ChatClient.send requires `username`. "
                "Your workspace expects MessageContext.username to be set."
            )

        # 2) Build contexts and mentions
        msg_context = MessageContext(
            username=username,
            timezone=timezone,
        )

        mention_context = MessageMentionContext(
            timezone=timezone,
        )

        mention = MessageMention(
            configurationId=agent,
            context=mention_context,
        )

        # 3) Create the user message
        msg: Message = self._conversations.create_message(
            conversation_id=conv_id,
            content=text,
            mentions=[mention],
            context=msg_context,
        )

        # 4) Wrap user message
        user_chat_msg = ChatMessage(
            role="user",
            text=msg.content or "",
            message_id=msg.sId,
            conversation_id=conv_id,
        )

        # 5) Stream events to build assistant reply
        assistant_chat_msg = self._wait_for_assistant_reply(
            conversation_id=conv_id,
            user_message_id=msg.sId,
            timeout=timeout,
        )

        return ChatResponse(
            conversation_id=conv_id,
            user_message=user_chat_msg,
            assistant_message=assistant_chat_msg,
        )

    # ------------------------------------------------------------------
    # Internal: streaming conversation events
    # ------------------------------------------------------------------

    def _wait_for_assistant_reply(
        self,
        *,
        conversation_id: str,
        user_message_id: str,
        timeout: float,
    ) -> Optional[ChatMessage]:
        """
        Wait for the assistant reply corresponding to `user_message_id`.

        Strategy:
          - Stream conversation events via ConversationsClient.stream_events.
          - First, detect the *agent* message id whose parentMessageId == user_message_id.
          - Then wait until we see AGENT_MESSAGE_DONE or AGENT_ERROR for that agent message.
          - Once done, re-fetch the conversation and extract the agent's text reply.

        Returns:
            ChatMessage for the assistant reply, or None if nothing
            could be gathered before timeout.

        Raises:
            ChatError on agent_error or streaming failures.
        """
        deadline = time.time() + timeout

        agent_message_id: Optional[str] = None
        done = False

        try:
            for event in self._conversations.stream_events(
                conversation_id,
                timeout=timeout,
            ):
                # Manual timeout guard (stream itself also has a timeout).
                if time.time() > deadline:
                    break

                etype = event.type
                # In case anything funky happens, normalise to string.
                if isinstance(etype, ConversationEventType):
                    etype_value = etype.value
                else:
                    etype_value = str(etype or "")

                # --- Step 1: find the agent message linked to this user message ---
                if (
                    etype_value == ConversationEventType.AGENT_MESSAGE_NEW.value
                    and event.message is not None
                ):
                    parent_id = getattr(event.message, "parentMessageId", None)
                    if parent_id == user_message_id:
                        agent_message_id = event.message.sId

                # Until we know which agent message we're following, skip.
                if agent_message_id is None:
                    continue

                # From here on, we only care about events for this agent message.
                if event.messageId != agent_message_id:
                    continue

                # --- Step 2: stop on done or error ---
                if etype_value == ConversationEventType.AGENT_ERROR.value:
                    err = getattr(event, "error", None)
                    if isinstance(err, dict):
                        msg = err.get("message") or repr(err)
                    else:
                        msg = str(err) if err is not None else "Unknown agent error"
                    raise ChatError(
                        f"Agent error while generating reply: {msg}"
                    )

                if etype_value == ConversationEventType.AGENT_MESSAGE_DONE.value:
                    done = True
                    break

        except ChatError:
            # Already a high-level chat error, just bubble up.
            raise
        except Exception as exc:
            # Wrap any lower-level streaming / parsing errors.
            raise ChatError(
                f"Error while streaming assistant reply: {exc}"
            ) from exc

        # If we never even discovered an agent message, there's nothing to return.
        if not done or agent_message_id is None:
            # No assistant content found within timeout or no agent
            # message linked to this user message.
            return None

        # At this point, either:
        # - done == True (we saw AGENT_MESSAGE_DONE), or
        # - we timed out but did at least see an AGENT_MESSAGE_NEW.
        # In both cases, we can try to read the latest conversation state.
        conv = self._conversations.get(conversation_id)

        # `conv.content` is a nested list of raw message dicts; we'll scan those.
        assistant_text: str = ""
        content_blocks = getattr(conv, "content", []) or []

        for block in content_blocks:
            if not isinstance(block, list):
                continue
            for obj in block:
                if not isinstance(obj, dict):
                    continue
                if (
                    obj.get("sId") == agent_message_id
                    and obj.get("type") == "agent_message"
                ):
                    assistant_text = obj.get("content") or ""
                    break
            if assistant_text:
                break

        if not assistant_text:
            # Could be a race or an agent that produced no text; in that
            # case we just return None, same as "no reply".
            return None

        return ChatMessage(
            role="assistant",
            text=assistant_text,
            message_id=agent_message_id,
            conversation_id=conversation_id,
        )