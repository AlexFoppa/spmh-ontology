#!/usr/bin/env python3
"""Add HURON/QASAR lexical formalism without changing TBox axioms.

- rdfs:label + rdfs:comment on imported dc/dcterms/rdfs/owl IRIs (Major/Minor)
- skos:altLabel from existing 'Synonyms:' text in rdfs:comment (DepressedMood, Fatigue)
- xml:lang/en on rdfs:label and rdfs:comment for SPMH schema entities missing language tags

Does not invent synonym terms. Does not alter class axioms, domains, ranges, or individuals.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, SKOS

ROOT = Path(__file__).resolve().parents[1]
SPMH_NS = "http://www.semanticweb.org/spmh/ontologies/2024/3/SPMH/"
SCHEMA_TYPES = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty}

IMPORTED_META: dict[URIRef, tuple[str, str]] = {
    DC.creator: ("creator", "Names the entity primarily responsible for making the resource."),
    DC.description: ("description", "Describes the resource in free text."),
    DC.title: ("title", "Names the resource."),
    DCTERMS.license: ("license", "Legal document giving official permission to do something with the resource."),
    RDFS.comment: ("comment", "Provides a human-readable description of a resource."),
    RDFS.label: ("label", "Provides a human-readable version of a resource name."),
    OWL.versionInfo: ("version information", "Annotation property for ontology version metadata."),
    SKOS.altLabel: ("alternative label", "Alternative lexical label for a resource."),
}

SYNONYM_TYPO_FIXES = {"Burrden": "Burden"}


def parse_synonyms_from_comment(comment: str) -> list[str]:
    match = re.search(r"Synonyms:\s*(.+)$", comment, flags=re.IGNORECASE)
    if not match:
        return []
    text = match.group(1).strip().rstrip(".")
    text = re.sub(r"\s+and\s+", ", ", text, count=1)
    terms = [part.strip() for part in text.split(",") if part.strip()]
    return [SYNONYM_TYPO_FIXES.get(term, term) for term in terms]


def schema_entities(g: Graph) -> set[URIRef]:
    entities: set[URIRef] = set()
    for t in SCHEMA_TYPES:
        for s in g.subjects(RDF.type, t):
            if isinstance(s, URIRef) and str(s).startswith(SPMH_NS):
                entities.add(s)
    return entities


def ensure_lang_en(g: Graph, subject: URIRef, predicate: URIRef) -> int:
    added = 0
    for o in list(g.objects(subject, predicate)):
        if not isinstance(o, Literal):
            continue
        if o.language:
            continue
        g.remove((subject, predicate, o))
        g.add((subject, predicate, Literal(str(o), lang="en")))
        added += 1
    return added


def patch_imported_vocabulary(g: Graph) -> int:
    added = 0
    for uri, (label, comment) in IMPORTED_META.items():
        if (uri, RDFS.label, None) not in g:
            g.add((uri, RDFS.label, Literal(label, lang="en")))
            added += 1
        if (uri, RDFS.comment, None) not in g:
            g.add((uri, RDFS.comment, Literal(comment, lang="en")))
            added += 1
    return added


def patch_synonyms_from_comments(g: Graph) -> int:
    added = 0
    for subject in schema_entities(g):
        if (subject, RDF.type, OWL.Class) not in g:
            continue
        for comment in g.objects(subject, RDFS.comment):
            if not isinstance(comment, Literal):
                continue
            for term in parse_synonyms_from_comment(str(comment)):
                literal = Literal(term, lang="en")
                if (subject, SKOS.altLabel, literal) in g:
                    continue
                g.add((subject, SKOS.altLabel, literal))
                added += 1
    return added


def patch_schema_language_tags(g: Graph) -> int:
    patched = 0
    for subject in schema_entities(g):
        patched += ensure_lang_en(g, subject, RDFS.label)
        patched += ensure_lang_en(g, subject, RDFS.comment)
    ont = URIRef(SPMH_NS.rstrip("/"))
    patched += ensure_lang_en(g, ont, RDFS.label)
    patched += ensure_lang_en(g, ont, DC.description)
    return patched


def bind_namespaces(g: Graph) -> None:
    g.bind("dc", DC)
    g.bind("dcterms", DCTERMS)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)


def patch_file(path: Path) -> Graph:
    g = Graph()
    fmt = "xml" if path.suffix == ".owl" else "turtle"
    g.parse(path, format=fmt)
    bind_namespaces(g)

    imported = patch_imported_vocabulary(g)
    synonyms = patch_synonyms_from_comments(g)
    lang_tags = patch_schema_language_tags(g)

    print(
        f"{path.name}: imported={imported}, altLabel={synonyms}, lang_tags={lang_tags}, "
        f"triples={len(g)}"
    )
    return g


def main() -> None:
    owl_path = ROOT / "SPMH-public.owl"
    ttl_path = ROOT / "SPMH-public.ttl"

    g = patch_file(owl_path)
    owl_xml = g.serialize(format="xml")
    owl_path.write_text(owl_xml, encoding="utf-8")

    ttl = g.serialize(format="turtle")
    ttl_path.write_text(ttl, encoding="utf-8")

    verify = Graph()
    verify.parse(owl_path, format="xml")
    verify.parse(data=ttl, format="turtle")
    print(f"Wrote {owl_path} ({len(owl_xml.encode())} bytes)")
    print(f"Wrote {ttl_path} ({len(ttl.encode())} bytes)")


if __name__ == "__main__":
    main()
