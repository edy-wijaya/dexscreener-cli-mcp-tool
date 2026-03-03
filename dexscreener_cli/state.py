from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from .config import DEFAULT_CHAINS, ScanFilters

TaskStatus = Literal["todo", "running", "done", "blocked"]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class ScanPreset:
    name: str
    chains: tuple[str, ...]
    limit: int
    min_liquidity_usd: float
    min_volume_h24_usd: float
    min_txns_h1: int
    min_price_change_h1: float
    created_at: str
    updated_at: str

    @classmethod
    def from_filters(cls, name: str, filters: ScanFilters) -> "ScanPreset":
        now = utc_now_iso()
        return cls(
            name=name,
            chains=filters.chains,
            limit=filters.limit,
            min_liquidity_usd=filters.min_liquidity_usd,
            min_volume_h24_usd=filters.min_volume_h24_usd,
            min_txns_h1=filters.min_txns_h1,
            min_price_change_h1=filters.min_price_change_h1,
            created_at=now,
            updated_at=now,
        )

    def to_filters(self) -> ScanFilters:
        return ScanFilters(
            chains=self.chains,
            limit=self.limit,
            min_liquidity_usd=self.min_liquidity_usd,
            min_volume_h24_usd=self.min_volume_h24_usd,
            min_txns_h1=self.min_txns_h1,
            min_price_change_h1=self.min_price_change_h1,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScanPreset":
        return cls(
            name=str(payload["name"]),
            chains=tuple(payload.get("chains", DEFAULT_CHAINS)),
            limit=int(payload.get("limit", 20)),
            min_liquidity_usd=float(payload.get("min_liquidity_usd", 35_000.0)),
            min_volume_h24_usd=float(payload.get("min_volume_h24_usd", 90_000.0)),
            min_txns_h1=int(payload.get("min_txns_h1", 80)),
            min_price_change_h1=float(payload.get("min_price_change_h1", 0.0)),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
        )

    def to_dict(self) -> dict[str, Any]:
        obj = asdict(self)
        obj["chains"] = list(self.chains)
        return obj


@dataclass(slots=True)
class ScanTask:
    id: str
    name: str
    preset: str | None
    filters: dict[str, Any] | None
    interval_seconds: int | None
    alerts: dict[str, Any] | None
    status: TaskStatus
    notes: str
    created_at: str
    updated_at: str
    last_run_at: str | None
    last_alert_at: str | None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        preset: str | None = None,
        filters: dict[str, Any] | None = None,
        interval_seconds: int | None = None,
        alerts: dict[str, Any] | None = None,
        status: TaskStatus = "todo",
        notes: str = "",
    ) -> "ScanTask":
        now = utc_now_iso()
        return cls(
            id=uuid4().hex[:10],
            name=name,
            preset=preset,
            filters=filters,
            interval_seconds=interval_seconds,
            alerts=alerts,
            status=status,
            notes=notes,
            created_at=now,
            updated_at=now,
            last_run_at=None,
            last_alert_at=None,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScanTask":
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            preset=payload.get("preset"),
            filters=payload.get("filters"),
            interval_seconds=payload.get("interval_seconds"),
            alerts=payload.get("alerts"),
            status=str(payload.get("status", "todo")),  # type: ignore[assignment]
            notes=str(payload.get("notes", "")),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            last_run_at=payload.get("last_run_at"),
            last_alert_at=payload.get("last_alert_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (Path.home() / ".dexscreener-cli")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.presets_file = self.base_dir / "presets.json"
        self.tasks_file = self.base_dir / "tasks.json"

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _save_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        tmp.replace(path)

    # Presets
    def list_presets(self) -> list[ScanPreset]:
        data = self._load_json(self.presets_file)
        rows = [ScanPreset.from_dict(p) for p in data.get("presets", [])]
        rows.sort(key=lambda p: p.name.lower())
        return rows

    def get_preset(self, name: str) -> ScanPreset | None:
        wanted = name.strip().lower()
        for preset in self.list_presets():
            if preset.name.lower() == wanted:
                return preset
        return None

    def save_preset(self, preset: ScanPreset) -> ScanPreset:
        rows = self.list_presets()
        existing = self.get_preset(preset.name)
        if existing:
            preset.created_at = existing.created_at
        preset.updated_at = utc_now_iso()
        new_rows = [p for p in rows if p.name.lower() != preset.name.lower()]
        new_rows.append(preset)
        new_rows.sort(key=lambda p: p.name.lower())
        self._save_json(self.presets_file, {"presets": [p.to_dict() for p in new_rows]})
        return preset

    def delete_preset(self, name: str) -> bool:
        rows = self.list_presets()
        new_rows = [p for p in rows if p.name.lower() != name.strip().lower()]
        if len(new_rows) == len(rows):
            return False
        self._save_json(self.presets_file, {"presets": [p.to_dict() for p in new_rows]})
        return True

    # Tasks
    def list_tasks(self, status: TaskStatus | None = None) -> list[ScanTask]:
        data = self._load_json(self.tasks_file)
        rows = [ScanTask.from_dict(t) for t in data.get("tasks", [])]
        if status:
            rows = [t for t in rows if t.status == status]
        rows.sort(key=lambda t: (t.status, t.updated_at), reverse=False)
        return rows

    def get_task(self, name_or_id: str) -> ScanTask | None:
        key = name_or_id.strip().lower()
        for task in self.list_tasks():
            if task.id.lower() == key or task.name.lower() == key:
                return task
        return None

    def create_task(
        self,
        *,
        name: str,
        preset: str | None = None,
        filters: dict[str, Any] | None = None,
        interval_seconds: int | None = None,
        alerts: dict[str, Any] | None = None,
        notes: str = "",
    ) -> ScanTask:
        rows = self.list_tasks()
        if any(t.name.lower() == name.lower() for t in rows):
            raise ValueError(f"Task '{name}' already exists")
        task = ScanTask.create(
            name=name,
            preset=preset,
            filters=filters,
            interval_seconds=interval_seconds,
            alerts=alerts,
            notes=notes,
        )
        rows.append(task)
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in rows]})
        return task

    def update_task_status(self, name_or_id: str, status: TaskStatus) -> ScanTask:
        rows = self.list_tasks()
        updated: ScanTask | None = None
        for task in rows:
            if task.id.lower() == name_or_id.lower() or task.name.lower() == name_or_id.lower():
                task.status = status
                task.updated_at = utc_now_iso()
                updated = task
                break
        if not updated:
            raise ValueError(f"Task '{name_or_id}' not found")
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in rows]})
        return updated

    def touch_task_run(self, name_or_id: str) -> ScanTask:
        rows = self.list_tasks()
        updated: ScanTask | None = None
        for task in rows:
            if task.id.lower() == name_or_id.lower() or task.name.lower() == name_or_id.lower():
                now = utc_now_iso()
                task.last_run_at = now
                task.updated_at = now
                updated = task
                break
        if not updated:
            raise ValueError(f"Task '{name_or_id}' not found")
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in rows]})
        return updated

    def touch_task_alert(self, name_or_id: str) -> ScanTask:
        rows = self.list_tasks()
        updated: ScanTask | None = None
        for task in rows:
            if task.id.lower() == name_or_id.lower() or task.name.lower() == name_or_id.lower():
                now = utc_now_iso()
                task.last_alert_at = now
                task.updated_at = now
                updated = task
                break
        if not updated:
            raise ValueError(f"Task '{name_or_id}' not found")
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in rows]})
        return updated

    def update_task(
        self,
        name_or_id: str,
        *,
        preset: str | None = None,
        filters: dict[str, Any] | None = None,
        interval_seconds: int | None = None,
        alerts: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> ScanTask:
        rows = self.list_tasks()
        updated: ScanTask | None = None
        for task in rows:
            if task.id.lower() == name_or_id.lower() or task.name.lower() == name_or_id.lower():
                task.preset = preset
                task.filters = filters
                task.interval_seconds = interval_seconds
                task.alerts = alerts
                if notes is not None:
                    task.notes = notes
                task.updated_at = utc_now_iso()
                updated = task
                break
        if not updated:
            raise ValueError(f"Task '{name_or_id}' not found")
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in rows]})
        return updated

    def delete_task(self, name_or_id: str) -> bool:
        rows = self.list_tasks()
        key = name_or_id.strip().lower()
        new_rows = [t for t in rows if t.id.lower() != key and t.name.lower() != key]
        if len(new_rows) == len(rows):
            return False
        self._save_json(self.tasks_file, {"tasks": [t.to_dict() for t in new_rows]})
        return True
