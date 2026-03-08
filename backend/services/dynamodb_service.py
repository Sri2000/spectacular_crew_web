"""
DynamoDB service — wraps boto3 for table creation and item operations.

Never raises; returns result dicts (same pattern as S3Service).
Tables are auto-created on first use if they don't exist.
"""
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import settings

logger = logging.getLogger(__name__)


def _to_dynamo(value: Any) -> Dict:
    """Convert a Python value to DynamoDB AttributeValue format."""
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, (int, float)):
        return {"N": str(value)}
    if isinstance(value, dict):
        return {"M": {k: _to_dynamo(v) for k, v in value.items()}}
    if isinstance(value, list):
        return {"L": [_to_dynamo(i) for i in value]}
    if value is None:
        return {"NULL": True}
    return {"S": str(value)}  # fallback: stringify


class DynamoDBService:
    """Thin wrapper around boto3 DynamoDB client."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        # Track tables confirmed to exist so we skip create_table on repeat calls
        self._ensured_tables: set = set()

    # ── Table management ──────────────────────────────────────────────────────

    def _ensure_table(
        self,
        table_name: str,
        hash_key: str,
        range_key: Optional[str] = None,
    ) -> bool:
        """Create table if it doesn't exist. Idempotent — safe to call repeatedly."""
        if table_name in self._ensured_tables:
            return True
        try:
            key_schema = [{"AttributeName": hash_key, "KeyType": "HASH"}]
            attr_defs = [{"AttributeName": hash_key, "AttributeType": "S"}]
            if range_key:
                key_schema.append({"AttributeName": range_key, "KeyType": "RANGE"})
                attr_defs.append({"AttributeName": range_key, "AttributeType": "S"})

            self._client.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attr_defs,
                BillingMode="PAY_PER_REQUEST",
            )
            logger.info("DynamoDB table created: %s — waiting for ACTIVE state", table_name)
            # Table creation is async; wait until it's ACTIVE before returning
            waiter = self._client.get_waiter("table_exists")
            waiter.wait(TableName=table_name, WaiterConfig={"Delay": 2, "MaxAttempts": 15})
            logger.info("DynamoDB table ACTIVE: %s", table_name)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "ResourceInUseException":
                # Table already exists — that's fine
                pass
            else:
                logger.error("DynamoDB create_table failed for %s: %s", table_name, exc)
                return False
        except (BotoCoreError, Exception) as exc:
            logger.error("DynamoDB create_table error for %s: %s", table_name, exc)
            return False

        self._ensured_tables.add(table_name)
        return True

    # ── Write ─────────────────────────────────────────────────────────────────

    def put_item(
        self,
        table_name: str,
        item: Dict[str, Any],
        hash_key: str = "id",
        range_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Put a Python dict item into DynamoDB.
        Auto-creates the table on first call. Never raises.

        Returns:
          {"success": True, "error": None}  on success
          {"success": False, "error": str}  on failure
        """
        if not self._ensure_table(table_name, hash_key, range_key):
            return {"success": False, "error": f"Table '{table_name}' could not be created or verified."}
        try:
            dynamo_item = {k: _to_dynamo(v) for k, v in item.items()}
            self._client.put_item(TableName=table_name, Item=dynamo_item)
            logger.info(
                "DynamoDB put_item OK | table=%s key=%s",
                table_name,
                item.get(hash_key),
            )
            return {"success": True, "error": None}
        except (BotoCoreError, ClientError) as exc:
            logger.error("DynamoDB put_item failed | table=%s: %s", table_name, exc)
            return {"success": False, "error": str(exc)}

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_item(
        self,
        table_name: str,
        key: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Get an item by primary key.
        Returns the raw DynamoDB Item dict, or None on miss / error.
        """
        try:
            dynamo_key = {k: _to_dynamo(v) for k, v in key.items()}
            resp = self._client.get_item(TableName=table_name, Key=dynamo_key)
            return resp.get("Item")
        except (BotoCoreError, ClientError) as exc:
            logger.error("DynamoDB get_item failed | table=%s: %s", table_name, exc)
            return None
