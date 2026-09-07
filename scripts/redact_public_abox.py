#!/usr/bin/env python3
"""Apply public-release anonymization to the SPMH A-box section."""

from __future__ import annotations

import re

REDACTED = "REDACTED"

# Quasi-identifiers on Person01 — preserve internal ID and generic relations.
PERSON_REDACT_PROPS = (
    "hasEducation",
    "hasEthnicity",
    "hasGender",
    "hasIncome",
)

# Literal substrings that must not appear in the public A-box after redaction.
FORBIDDEN_LITERALS = (
    "Technologist with a focus on health",
    "Master's student in IT",
    "Designer and RPG enthusiast",
    "Caucasian",
    '"34"^^xsd:positiveInteger',
    ':hasEducation "master\'s student"',
    ':hasGender "Male"',
    ':hasIncome "classified"',
)


def _redact_person_attributes(text: str) -> str:
    text = re.sub(r"\s*:hasAge\s+[^;\n]+;\s*\n", "\n", text)
    for prop in PERSON_REDACT_PROPS:
        text = re.sub(
            rf"(:{prop}\s+)(?:\"[^\"]*\"(?:\^\^xsd:\w+\s*)?|-?\d+(?:\.\d+)?(?:\^\^xsd:\w+\s*)?)\s*;",
            rf'\1"{REDACTED}" ;',
            text,
            flags=re.IGNORECASE,
        )
    return text


def _redact_profile_bio(text: str) -> str:
    text = re.sub(
        r'(:ProfileID1\b[\s\S]*?:hasTextContent\s+)"""[\s\S]*?"""\s*;',
        rf'\1"{REDACTED}" ;',
        text,
        count=1,
    )
    text = re.sub(
        r'(:ProfileID1\b[\s\S]*?:hasTextContent\s+)"(?:[^"\\]|\\.)*"\s*;',
        rf'\1"{REDACTED}" ;',
        text,
        count=1,
    )
    return text


def redact_abox_text(text: str) -> str:
    text = _redact_person_attributes(text)
    text = _redact_profile_bio(text)
    return text


def assert_redaction(text: str) -> None:
    lowered = text.lower()
    for needle in FORBIDDEN_LITERALS:
        if needle.lower() in lowered:
            raise AssertionError(f"Public A-box still contains forbidden literal: {needle!r}")
    if re.search(r":hasAge\s+", text):
        raise AssertionError("Public A-box still contains hasAge")
    if "technologist" in lowered:
        raise AssertionError("Public A-box still contains profile bio quasi-identifiers")
