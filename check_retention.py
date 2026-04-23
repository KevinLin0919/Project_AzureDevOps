from dotenv import load_dotenv
load_dotenv()

from asgards.src._auth import _build_connection
import os

connection = _build_connection(os.getenv("AZURE_DEVOPS_PAT"), os.getenv("AZURE_DEVOPS_ORG_URL"))
client = connection.clients.get_build_client()

settings = client.get_build_settings("Kevin_test")
print("=== default_retention_policy ===")
d = settings.default_retention_policy
if d:
    print(vars(d))

print("=== maximum_retention_policy ===")
m = settings.maximum_retention_policy
if m:
    print(vars(m))

print("=== top-level ===")
print("days_to_keep_deleted_builds_before_destroy:", settings.days_to_keep_deleted_builds_before_destroy)
