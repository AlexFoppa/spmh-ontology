#!/usr/bin/env python3
"""Align public A-box instances with Tables 17/18 (authoritative property domains)."""

from __future__ import annotations

import re

PUBLICATION_ENTITIES = re.compile(r"^(?:PostID\d+|ProfileID1)$")
ARTIFACT_ENTITIES = re.compile(r"^Artifact\d+$")
TRACE_ENTITIES = re.compile(r"^Trace\d+$")


def _entity_from_header(line: str) -> str | None:
    match = re.search(r"/SPMH/(\w+)\s*$", line)
    return match.group(1) if match else None


def fix_abox_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    entity: str | None = None

    for line in lines:
        if line.startswith("###"):
            entity = _entity_from_header(line)
            out.append(line)
            continue

        if entity == "AccountID1":
            line = line.replace(":hasUrl", ":hasAccountUrl")
        elif entity and ARTIFACT_ENTITIES.match(entity):
            line = line.replace(":hasMoment", ":hasCreationMoment")
        elif entity and PUBLICATION_ENTITIES.match(entity):
            line = line.replace(":comesFromSocialPlataform", ":publishedInSocialPlatform")
            line = line.replace(":isAbout :AccountID1", ":isAbout :Person01")
        elif entity and TRACE_ENTITIES.match(entity):
            line = line.replace(":isResultOf :LLMTraceDetection", ":isFoundUsing :LLMTraceDetection")
        elif entity == "LLMTraceDetection":
            if ":isResultOf" in line or ":hasExplanation" in line:
                continue
            if re.search(r":Analisys\s*;\s*$", line):
                line = re.sub(r":Analisys\s*;\s*$", ":Analisys .\n", line)

        out.append(line)

    return "".join(out)


def assert_abox_consistency(text: str) -> None:
    if ":hasAge" in text:
        raise AssertionError("Public A-box still declares hasAge on Person01")
    if ":isAbout :AccountID1" in text:
        raise AssertionError("Publication still uses isAbout :AccountID1")
    account = re.search(r":AccountID1 rdf:type[\s\S]*?^\.\s*$", text, re.M)
    if account and ":hasUrl" in account.group(0):
        raise AssertionError("AccountID1 still uses hasUrl instead of hasAccountUrl")
    for num in range(1, 20):
        block = re.search(rf":Artifact{num:02d} rdf:type[\s\S]*?^\.\s*$", text, re.M)
        if block and ":hasMoment" in block.group(0):
            raise AssertionError(f"Artifact{num:02d} still uses hasMoment")
    if re.search(r":Trace\d+ rdf:type[\s\S]*?:isResultOf :LLMTraceDetection", text, re.M):
        raise AssertionError("Trace still uses isResultOf :LLMTraceDetection")
    llm = re.search(r":LLMTraceDetection rdf:type[\s\S]*?^\.\s*$", text, re.M)
    if llm and re.search(r":(?:isResultOf|hasExplanation)", llm.group(0)):
        raise AssertionError("LLMTraceDetection still has invalid isResultOf/hasExplanation")
    if not re.search(r":Trace\d+ rdf:type[\s\S]*?:isFoundUsing :LLMTraceDetection", text, re.M):
        raise AssertionError("Expected Trace isFoundUsing :LLMTraceDetection links")
