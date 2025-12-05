# examples/conversations.py

from dotenv import load_dotenv

from dust_client import DustClient, DustConfig
from dust_client.conversations.models import MessageMention, MessageMentionContext, MessageContext


def main() -> None:
    load_dotenv()
    config = DustConfig.from_env()
    client = DustClient(config)

    client.validate()

    # 1) Create a conversation
    conv = client.conversations.create(
        title="SDK test conversation",
        # model is optional; you can also leave it to the agent side
        model="claude-3-5-sonnet-20240620",
    )
    print("Conversation:", conv.sId, conv.title)

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
        blocking=True,
    )
    print("Message:", msg.sId, msg.author_name, msg.content)

    client.close()


if __name__ == "__main__":
    main()