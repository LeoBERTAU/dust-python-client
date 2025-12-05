# examples/chat.py

from dotenv import load_dotenv
from dust_client import DustClient, DustConfig

def main() -> None:
    load_dotenv()
    config = DustConfig.from_env()
    client = DustClient(config)

    client.validate()

    # One-shot
    resp = client.chat.send(
        agent="dust",              # agent sId
        text="Hello from ChatClient!",
        username="leo",
        timezone="Europe/Paris",
    )
    print("Conversation:", resp.conversation_id)
    print("User:", resp.user_message.text)
    print("Assistant:", resp.assistant_message)  # currently None

    # Session
    session = client.chat.session(
        agent="dust",
        username="leo",
        timezone="Europe/Paris",
        title="ChatClient test",
    )

    r2 = session.send("Can you summarize what ChatClient does?")
    print("Session conversation:", r2.conversation_id)
    print("User:", r2.user_message.text)

    client.close()

if __name__ == "__main__":
    main()