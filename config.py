import os
from dotenv import load_dotenv

load_dotenv()

MEMCLAW_API_KEY = os.environ["MEMCLAW_API_KEY"]
MEMCLAW_TENANT_ID = os.environ["MEMCLAW_TENANT_ID"]
MEMCLAW_BASE_URL = os.getenv("MEMCLAW_BASE_URL", "https://memclaw.net/api/v1")

FLEET_ORG_SHARED = "fleet-org-shared"
FLEET_SALES = "fleet-sales"
FLEET_LEGAL = "fleet-legal"

AGENT_SALES = "sales-agent-1"
AGENT_LEGAL = "legal-agent-1"
AGENT_ADMIN = "admin-agent"

AISA_API_KEY = os.getenv("AISA_API_KEY", "")
AISA_BASE_URL = os.getenv("AISA_BASE_URL", "https://api.aisa.one/v1")
AISA_MODEL = os.getenv("AISA_MODEL", "claude-opus-4-7")
