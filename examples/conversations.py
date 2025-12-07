# examples/conversations.py

from dotenv import load_dotenv

from dust_client import DustClient, DustConfig
from dust_client.conversations.models import (
    MessageMention,
    MessageMentionContext,
    MessageContext,
    ConversationEventType,
)
from dust_client.exceptions import DustBadRequestError


def main() -> None:
    load_dotenv()
    config = DustConfig.from_env()
    client = DustClient(config)

    # Optional but nice to fail fast if credentials are wrong
    client.validate()

    # 1) Create a conversation
    conv = client.conversations.create(
        title="SDK test conversation",
        blocking=True,
    )
    print("Created conversation:", conv.sId, conv.title)

    # 2) Send a message to an agent
    agent_id = "helper"

    mention_ctx = MessageMentionContext(timezone="Europe/Paris")
    mention = MessageMention(configurationId=agent_id, context=mention_ctx)
    ctx = MessageContext(timezone="Europe/Paris", username="leo")

    msg = client.conversations.create_message(
        conv.sId,
        content="Hello from the Python SDK!",
        mentions=[mention],
        context=ctx,
    )
    print("Created message:", msg.sId, msg.author_name, msg.content)

    # 3) Get the conversation details
    conv_fetched = client.conversations.get(conv.sId)
    print("\nFetched conversation object:")
    print(conv_fetched)

    # 4) Try to edit the message (expected to fail due to Dust limitation)
    print("\nAttempting to edit the message...")
    try:
        edited = client.conversations.edit_message(
            conv.sId,
            msg.sId,
            content="Hello again, edited via edit_message!",
            mentions=[mention],
        )
        print("Edited message:", edited.sId, edited.content)
    except DustBadRequestError as e:
        # NOTE: This is expected to fail with current Dust behaviour
        # when the message already has mentions (has triggered an agent).
        print("Edit failed (expected):")
        print(e)
        print(
            "\nNote: Dust currently does not support editing messages that "
            "already have agent mentions (and thus have triggered an agent)."
        )

    # 5) Stream conversation-level events only
    print("\nStreaming conversation events:")
    for event in client.conversations.stream_events(conv.sId):
        print("Event:", event.type, getattr(event, "messageId", None))

        # stop after we observe the final agent output
        if event.type in (
            ConversationEventType.AGENT_MESSAGE_DONE,
            ConversationEventType.AGENT_ERROR,
        ):
            break

    # 6) Demonstrate cancel_messages
    # (By this time the agent is likely already done, so this is mostly a demo.)
    print("\nSending cancel for the user message (demo only):")
    cancel_result = client.conversations.cancel_messages(
        conv.sId,
        [msg.sId],
    )
    print("Cancel result:", cancel_result)

    client.close()


if __name__ == "__main__":
    main()
