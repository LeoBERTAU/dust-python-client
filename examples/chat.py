# examples/chat.py

from dotenv import load_dotenv

from dust_client import DustClient, DustConfig

AGENT_SID = "gpt-5-nano"

def main() -> None:
    load_dotenv()
    config = DustConfig.from_env()
    client = DustClient(config)

    client.validate()

    resp = client.chat.send(
        agent=AGENT_SID,
        text="Hello from ChatClient!",
        username="leo",  # or whatever makes sense in your workspace
        timezone="Europe/Paris",
        title="ChatClient demo",
    )

    print("Conversation ID:", resp.conversation_id)
    print("User message:", resp.user_message.text)

    if resp.assistant_message:
        print("Assistant message:", resp.assistant_message.text)
    else:
        print("Assistant message: <none>")

    client.close()


if __name__ == "__main__":
    main()