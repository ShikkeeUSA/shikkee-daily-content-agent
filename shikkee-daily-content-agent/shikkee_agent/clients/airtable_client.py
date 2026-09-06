"""
Thin wrapper over the Airtable REST API (https://airtable.com/developers/web/api).
Airtable is the pipeline's system of record for content + status -- it does NOT
gate publishing (Metricool draft / WordPress draft do that).
"""
from __future__ import annotations

import requests
from shikkee_agent.config import settings

API_ROOT = "https://api.airtable.com/v0"


class AirtableClient:
    def __init__(self, api_key: str | None = None, base_id: str | None = None):
        self.api_key = api_key or settings.airtable_api_key
        self.base_id = base_id or settings.airtable_base_id
        if not self.api_key:
            raise RuntimeError("AIRTABLE_API_KEY is not set")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def list_records(
        self,
        table_id: str,
        formula: str | None = None,
        sort: list[dict] | None = None,
        max_records: int | None = None,
        fields: list[str] | None = None,
    ) -> list[dict]:
        records: list[dict] = []
        offset = None
        while True:
            params: dict = {}
            if formula:
                params["filterByFormula"] = formula
            if sort:
                for i, s in enumerate(sort):
                    params[f"sort[{i}][field]"] = s["field"]
                    params[f"sort[{i}][direction]"] = s.get("direction", "asc")
            if max_records:
                params["maxRecords"] = max_records
            if fields:
                params["fields[]"] = fields
            if offset:
                params["offset"] = offset

            resp = requests.get(
                f"{API_ROOT}/{self.base_id}/{table_id}",
                headers=self._headers(),
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        return records

    def create_records(self, table_id: str, records: list[dict], typecast: bool = True) -> list[dict]:
        out = []
        for i in range(0, len(records), 10):  # Airtable caps batch creates at 10
            chunk = records[i : i + 10]
            resp = requests.post(
                f"{API_ROOT}/{self.base_id}/{table_id}",
                headers=self._headers(),
                json={"records": [{"fields": r} for r in chunk], "typecast": typecast},
                timeout=30,
            )
            resp.raise_for_status()
            out.extend(resp.json()["records"])
        return out

    def update_records(self, table_id: str, records: list[dict], typecast: bool = True) -> list[dict]:
        """records: [{"id": "rec...", "fields": {...}}, ...]"""
        out = []
        for i in range(0, len(records), 10):
            chunk = records[i : i + 10]
            resp = requests.patch(
                f"{API_ROOT}/{self.base_id}/{table_id}",
                headers=self._headers(),
                json={"records": chunk, "typecast": typecast},
                timeout=30,
            )
            resp.raise_for_status()
            out.extend(resp.json()["records"])
        return out

    def log_content(
        self,
        publish_date: str,
        platform: str,
        notes: str,
        caption: str,
        status: str = "draft",
        submitted_by: str = "Claude",
    ) -> dict:
        """Convenience wrapper matching the Content Pipeline table's schema."""
        fields = {
            "Publish date": publish_date,
            "platform": platform,
            "Founder account": notes,  # repurposed as a free-text notes field
            "caption": caption,
            "status": status,
            "submmited by": submitted_by,
        }
        return self.create_records(settings.airtable_content_table_id, [fields])[0]
