from dotenv import load_dotenv
load_dotenv()

from asgards.src._auth import _build_connection
import os

connection = _build_connection(os.getenv("AZURE_DEVOPS_PAT"), os.getenv("AZURE_DEVOPS_ORG_URL"))
policy_client = connection.clients.get_policy_client()

types = policy_client.get_policy_types("Kevin_test")
for t in types:
    print(f"{t.display_name}: {t.id}")
