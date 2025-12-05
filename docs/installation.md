# Installation

## Prerequisites

- Python **3.9+**
- A Dust workspace and API key
- `pip` and a virtual environment (recommended)

---

## Install for Development

For now, the recommended way is to install directly from the repository:

```bash
git clone https://github.com/LeoBERTAU/dust-python-client.git
cd dust-python-client
pip install -e ".[dev]"
```

This installs:
- dust_client (the SDK)
- Dev tools: pytest, ruff, python-dotenv

---

## (Future) Install from PyPI

Once the package is published:
```bash
pip install dust-client
```
Then you can import it:
```python
from dust_client import DustClient, DustConfig
```

---

## Environment variables

The SDK can read credentials from environment variables:
- DUST_WORKSPACE_ID
- DUST_API_KEY

Example:
```bash
export DUST_WORKSPACE_ID=your-workspace-id
export DUST_API_KEY=your-api-key
```
Then:
```python
from dust_client import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)
client.validate()
```

---

## Verifying the installation

Run a simple script:
```python
from dust_client import DustClient, DustConfig

client = DustClient(DustConfig.from_env())
client.validate()

print("Dust client is working!")
```
If your credentials are valid, you should see:
```code
Dust client is working!
```

