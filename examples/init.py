# examples/init.py

from dust_client import DustClient, DustConfig, DustError, DustAPIError


def main() -> None:
    # Option 1: load from environment
    # export DUST_WORKSPACE_ID=...
    # export DUST_API_KEY=...
    # config = DustConfig.from_env()

    # Option 2: explicit initialization
    config = DustConfig(
        base_url="https://eu.dust.tt",
        workspace_id="n9puyOJxmD",
        api_key="sk-58c90137b8847b0500bcfba298352bd8",
    )

    client = DustClient(config)

    try:
        client.validate()
        print("Client configuration is valid!")
    except (DustError, DustAPIError) as e:
        print("Configuration is invalid:", e)

    client.close()


if __name__ == "__main__":
    main()
