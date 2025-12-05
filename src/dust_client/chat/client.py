# dust_sdk/chat/client.py

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ..config import DustConfig
from ..exceptions import DustError
from ..conversations.models import (
    Message,
    MessageContext,
    MessageMention,
    MessageMentionContext,
)
from .models import ChatMessage, ChatResponse

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

    def send(
        self,
        text: str,
    ) -> ChatResponse:
        """
        Send a message within this session's conversation using the bound agent.

        Currently blocking-only: we wait for the message to be accepted, and
        return a ChatResponse describing the user message.

        In a future iteration, this will also attach the assistant_message once
        we aggregate conversation events.
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

    Initially, only blocking mode is implemented: we send a message and wait for
    the Dust API to accept it. In a later phase, we'll add assistant aggregation
    (via conversation events) and streaming.
    """

    def __init__(
        self,
        *,
        conversations: "ConversationsClient",
        agents: "AgentsClient",
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
    ) -> ChatResponse:
        """
        One-shot chat call.

        - If `conversation_id` is None, this creates a new conversation.
        - Otherwise, it sends the message in the existing conversation.
        - Uses `blocking=True` on the Conversations API to ensure the agent
          finishes processing before returning (even though we don't yet
          aggregate its reply).

        Args:
            agent: Agent configuration sId (e.g. "dust", "i5cIwRsG0u").
            text: User message content.
            username: Logical username for this user (required by Dust in most workspaces).
            timezone: Optional timezone; if None, may fall back to config defaults
                      in a future iteration.
            conversation_id: Optional existing conversation sId.
            title: Optional conversation title (only used when creating a new conversation).

        Returns:
            ChatResponse describing the user message and conversation_id.

        Raises:
            DustError / DustAPIError on API failures.
        """
        return self._send_internal(
            agent=agent,
            text=text,
            username=username,
            timezone=timezone,
            conversation_id=conversation_id,
            title=title,
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
    ) -> ChatResponse:
        """
        Core implementation used by both ChatClient.send and ChatSession.send.

        It:
          - ensures we have a conversationId
          - builds MessageContext + MessageMention
          - calls ConversationsClient.create_message with blocking=True
          - wraps the resulting Message into ChatMessage / ChatResponse

        For now, only the user message is exposed. Assistant message aggregation
        will come later once we build on top of conversation events.
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

        # 3) Create the message (blocking)
        msg: Message = self._conversations.create_message(
            conversation_id=conv_id,
            content=text,
            mentions=[mention],
            context=msg_context,
            blocking=True,
        )

        # 4) Wrap as high-level ChatMessage
        user_chat_msg = ChatMessage(
            role="user",
            text=msg.content,
            message_id=msg.sId,
            conversation_id=conv_id,
        )

        # NOTE:
        # - assistant_message is left as None for now.
        # - once we wire events ("Get the events for a conversation" / message events),
        #   we'll be able to attach a proper assistant ChatMessage as well.
        return ChatResponse(
            conversation_id=conv_id,
            user_message=user_chat_msg,
            assistant_message=None,
        )