# examples/agents.py

from dotenv import load_dotenv
from dust_client import DustClient, DustConfig, DustAPIError


# Initialize DustClient from environment variables
load_dotenv()
config = DustConfig.from_env()  # or explicit params
client = DustClient(config)

client.validate()


def list_agents() -> None:
    try:
        agents = client.agents.list()
        print(agents)
        print(f"Found {len(agents)} agents")
        for a in agents:
            print("-", a.name, f"(sId={a.sId})")
    except DustAPIError as e:
        print("Dust API error:", e)
        if e.details:
            print("Details:", e.details)


def get_agent(agent_id: str) -> None:
    try:
        agent = client.agents.get(agent_id)
        print(agent)
    except DustAPIError as e:
        print("Dust API error:", e)
        if e.details:
            print("Details:", e.details)


def search_agent_by_name(name: str) -> None:
    try:
        agents = client.agents.search(q=name)
        print(agents)
    except DustAPIError as e:
        print("Dust API error:", e)
        if e.details:
            print("Details:", e.details)


if __name__ == "__main__":
    list_agents()
    get_agent("i5cIwRsG0u")
    client.agents.get("i5cIwRsG0")
    search_agent_by_name("promptWriter")
