"""JSON Schema for Agent Memory state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


RECORD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "text", "status", "confidence", "salience"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "text": {"type": "string"},
        "type": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["active", "tentative", "candidate", "superseded", "stale", "closed", "parked"],
        },
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "salience": {"type": "integer", "minimum": 1, "maximum": 5},
        "evidence": {"type": "string"},
        "source": {"type": "string", "enum": ["agent", "derived", "external", "system", "tool", "user"]},
        "scope": {"type": "string", "enum": ["agent", "global", "organization", "project", "role", "user"]},
        "expires_at": {"type": "string"},
        "supersedes": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": True,
}

RECORD_REF: dict[str, Any] = {"$ref": "#/$defs/record"}

STATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/agent-memory-skill/agent-memory-skill/schemas/state.schema.json",
    "title": "Agent Memory State",
    "type": "object",
    "required": [
        "version",
        "updated_at",
        "user_profile",
        "project",
        "threads",
        "decisions",
        "episodes",
        "migration",
    ],
    "properties": {
        "version": {"type": "integer", "minimum": 1},
        "revision": {"type": "integer", "minimum": 0},
        "updated_at": {"type": "string"},
        "user_profile": {
            "type": "object",
            "required": ["preferences", "working_style", "avoid"],
            "properties": {
                "preferences": {"type": "array", "items": RECORD_REF},
                "working_style": {"type": "array", "items": RECORD_REF},
                "avoid": {"type": "array", "items": RECORD_REF},
            },
            "additionalProperties": True,
        },
        "project": {
            "type": "object",
            "required": ["name", "objective", "facts", "artifacts"],
            "properties": {
                "name": {"type": "string"},
                "objective": {"type": "string"},
                "facts": {"type": "array", "items": RECORD_REF},
                "artifacts": {"type": "array", "items": RECORD_REF},
            },
            "additionalProperties": True,
        },
        "threads": {
            "type": "object",
            "required": ["active", "open", "parked", "closed_recently"],
            "properties": {
                "active": {"anyOf": [RECORD_REF, {"type": "null"}]},
                "open": {"type": "array", "items": RECORD_REF},
                "parked": {"type": "array", "items": RECORD_REF},
                "closed_recently": {"type": "array", "items": RECORD_REF},
            },
            "additionalProperties": True,
        },
        "decisions": {"type": "array", "items": RECORD_REF},
        "episodes": {"type": "array", "items": RECORD_REF},
        "migration": {
            "type": "object",
            "required": ["summary", "next_actions", "risks", "handoff_notes"],
            "properties": {
                "summary": {"type": "string"},
                "next_actions": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
                "handoff_notes": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        },
    },
    "$defs": {"record": RECORD_SCHEMA},
    "additionalProperties": True,
}


def state_schema() -> dict[str, Any]:
    return deepcopy(STATE_SCHEMA)
