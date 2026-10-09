"""Typed task bodies; API-controlled fields cannot be modified through a raw payload."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

TaskType = Literal["habit", "daily", "todo", "reward"]
TaskFilter = Literal["habits", "dailys", "todos", "rewards", "completedTodos"]


class Difficulty(float, Enum):
    TRIVIAL = 0.1
    EASY = 1
    MEDIUM = 1.5
    HARD = 2


Frequency = Literal["daily", "weekly", "monthly", "yearly"]
Weekday = Literal["su", "m", "t", "w", "th", "f", "s"]
Text = Annotated[str, Field(min_length=1, max_length=5000, pattern=r"\S")]


class ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Text
    completed: bool = False


class TaskFields(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    text: Text | None = None
    notes: str | None = None
    priority: Difficulty | None = None
    tags: list[UUID] | None = None
    attribute: Literal["str", "int", "per", "con"] | None = None
    alias: Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")] | None = (
        None
    )
    due_date: date | datetime | None = Field(default=None, alias="date")
    frequency: Frequency | None = None
    every_x: Annotated[int, Field(ge=0, le=9999)] | None = Field(
        default=None, alias="everyX"
    )
    repeat: dict[Weekday, bool] | None = None
    start_date: date | datetime | None = Field(default=None, alias="startDate")
    days_of_month: list[Annotated[int, Field(ge=1, le=31)]] | None = Field(
        default=None, alias="daysOfMonth"
    )
    weeks_of_month: list[int] | None = Field(default=None, alias="weeksOfMonth")
    up: bool | None = None
    down: bool | None = None
    value: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    collapse_checklist: bool | None = Field(default=None, alias="collapseChecklist")

    def api_body(self) -> dict:
        """Omit absent values, preserve explicit empty lists/strings and false."""
        body = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "due_date" in self.model_fields_set and self.due_date is None:
            body["date"] = None
        return body

    def validate_for_type(self, task_type: str) -> None:
        body = self.api_body()
        groups = {
            "todo": {"date"},
            "daily": {
                "frequency",
                "everyX",
                "repeat",
                "startDate",
                "daysOfMonth",
                "weeksOfMonth",
            },
            "habit": {"up", "down"},
            "reward": {"value"},
        }
        for kind, fields in groups.items():
            if task_type != kind and body.keys() & fields:
                raise ValueError(
                    f"字段 {', '.join(sorted(body.keys() & fields))} 仅适用于 {kind}。"
                )
        if task_type not in {"daily", "todo"} and "collapseChecklist" in body:
            raise ValueError("清单仅适用于 daily 或 todo。")


class TaskCreate(TaskFields):
    type: TaskType
    text: Text
    checklist: list[ChecklistItem] | None = None

    @model_validator(mode="after")
    def validate_task(self) -> TaskCreate:
        self.validate_for_type(self.type)
        if self.checklist is not None and self.type not in {"daily", "todo"}:
            raise ValueError("清单仅适用于 daily 或 todo。")
        if self.type == "habit" and self.up is False and self.down is False:
            raise ValueError("habit 的 up 和 down 至少启用一个。")
        return self


class TaskUpdate(TaskFields):
    @model_validator(mode="after")
    def validate_update(self) -> TaskUpdate:
        if not self.api_body():
            raise ValueError("至少提供一个要修改的字段；清空请使用空字符串或空列表。")
        return self
