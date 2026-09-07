#!/usr/bin/env python3
"""Build SPMH v1.0.2: OOPS-clean schema + redacted A-box + HURON annotations.

Outputs:
  SPMH-public.owl  — RDF/XML (canonical; QASAR + OOPS!)
  SPMH-public.ttl  — Turtle export of the same ontology
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
UPDATED = Path("/home/alfoppa/Downloads/CSV teste original/Updated_SPMH.ttl")
PUBLIC_ABOX = Path("/home/alfoppa/Downloads/SPMH.ttl")
OUT_TTL = ROOT / "SPMH-public.ttl"
OUT_OWL = ROOT / "SPMH-public.owl"

OLD_NS = "http://www.semanticweb.org/alfoppa/ontologies/2024/3/SPMH/"
NEW_NS = "http://www.semanticweb.org/spmh/ontologies/2024/3/SPMH/"
NEW_ONT = URIRef(NEW_NS.rstrip("/"))
OLD_ONT = URIRef(OLD_NS.rstrip("/"))
CC_BY_40 = URIRef("https://creativecommons.org/licenses/by/4.0/")

SCHEMA_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.Ontology,
    OWL.AnnotationProperty,
    RDFS.Class,
}


def remap(uri: URIRef) -> URIRef:
    return URIRef(str(uri).replace(OLD_NS, NEW_NS))


def is_individual(g: Graph, node: URIRef) -> bool:
    for _, _, o in g.triples((node, RDF.type, None)):
        if o == OWL.NamedIndividual:
            return True
        if o in SCHEMA_TYPES:
            return False
        if isinstance(o, URIRef):
            return True
    return False


def individuals(g: Graph) -> set[URIRef]:
    return {s for s in g.subjects() if isinstance(s, URIRef) and is_individual(g, s)}


def copy_schema(src: Graph, dst: Graph, skip: set[URIRef]) -> None:
    for s, p, o in src:
        if s in skip:
            continue
        if isinstance(o, URIRef) and o in skip:
            continue
        if p == RDF.type and o == OWL.NamedIndividual:
            continue
        if s == OWL.topDataProperty and o == OWL.topDataProperty:
            continue
        rs = remap(s) if isinstance(s, URIRef) else s
        ro = remap(o) if isinstance(o, URIRef) else o
        dst.add((rs, p, ro))


def copy_individuals(src: Graph, dst: Graph, keep: set[URIRef]) -> None:
    for s, p, o in src:
        if s not in keep:
            continue
        dst.add((s, p, o))


def add_public_ontology_header(dst: Graph, src_public: Graph) -> None:
    for t in list(dst.triples((OLD_ONT, None, None))):
        dst.remove(t)
    for p, o in src_public.predicate_objects(NEW_ONT):
        if p == RDF.type:
            continue
        dst.add((NEW_ONT, p, o))
    dst.set((NEW_ONT, RDF.type, OWL.Ontology))
    dst.set((NEW_ONT, OWL.versionInfo, Literal("1.0.4")))
    dst.set((NEW_ONT, DCTERMS.license, CC_BY_40))


def add_oops_schema_fixes(dst: Graph) -> None:
    """P30: Storage (procedure) and Memory (cognition) are homonyms, not equivalents."""
    storage = URIRef(NEW_NS + "Storage")
    memory = URIRef(NEW_NS + "Memory")
    dst.set((storage, OWL.disjointWith, memory))
    dst.set(
        (
            memory,
            RDFS.comment,
            Literal(
                "Difficulty retrieving memories, a cognitive symptom associated with depression.",
                lang="en",
            ),
        )
    )
    dst.set((memory, RDFS.label, Literal("Memory difficulty", lang="en")))
    dst.set(
        (
            storage,
            RDFS.comment,
            Literal(
                "Procedure step for storing collected digital evidence with integrity controls.",
                lang="en",
            ),
        )
    )
    dst.set((storage, RDFS.label, Literal("Evidence storage procedure", lang="en")))


def add_platform_alias(dst: Graph) -> None:
    platform = URIRef(NEW_NS + "comesFromSocialPlatform")
    plataform = URIRef(NEW_NS + "comesFromSocialPlataform")
    if (platform, RDF.type, OWL.DatatypeProperty) not in dst:
        return
    for p, o in dst.predicate_objects(platform):
        if p == RDF.type:
            continue
        if (plataform, p, o) not in dst:
            dst.add((plataform, p, o))
    dst.add((plataform, RDF.type, OWL.DatatypeProperty))
    dst.add((plataform, OWL.equivalentProperty, platform))


def build_graph() -> Graph:
    updated = Graph()
    updated.parse(UPDATED, format="turtle")
    public = Graph()
    public.parse(PUBLIC_ABOX, format="turtle")

    updated_inds = individuals(updated)
    public_inds = individuals(public)

    out = Graph()
    out.bind("dc", DC)
    out.bind("dcterms", DCTERMS)
    out.bind("owl", OWL)
    out.bind("rdf", RDF)
    out.bind("rdfs", RDFS)
    out.bind("xsd", XSD)
    out.bind("", NEW_NS)

    copy_schema(updated, out, updated_inds)
    copy_individuals(public, out, public_inds)
    add_public_ontology_header(out, public)
    add_oops_schema_fixes(out)
    add_platform_alias(out)
    return out


def load_abox_section() -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    from fix_public_abox import assert_abox_consistency, fix_abox_text
    from redact_public_abox import assert_redaction, redact_abox_text

    text = PUBLIC_ABOX.read_text(encoding="utf-8")
    _, abox = text.split("#    Individuals", 1)
    abox = abox.split("###  Generated by the OWL API", 1)[0]
    abox = re.sub(r"^#################################################################\s*\n", "", abox, count=1)
    abox = redact_abox_text(abox)
    abox = fix_abox_text(abox)
    assert_redaction(abox)
    assert_abox_consistency(abox)
    return (
        "\n#################################################################\n"
        "#    Individuals\n"
        "#################################################################\n"
        + abox.lstrip("\n")
    )


def flatten_multiline_literals(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        body = body.replace("\\", "\\\\").replace('"', '\\"')
        body = re.sub(r"\s*\n\s*", r"\\n", body)
        return f'"{body}"'

    return re.sub(r'"""([\s\S]*?)"""', repl, text)


def serialize_schema_protege(g: Graph) -> str:
    inds = individuals(g)
    schema = Graph()
    for prefix, ns in g.namespace_manager.namespaces():
        schema.bind(prefix, ns)
    for s, p, o in g:
        if s in inds or (isinstance(o, URIRef) and o in inds):
            continue
        schema.add((s, p, o))

    raw = schema.serialize(format="turtle")
    raw = raw.replace(OLD_NS, NEW_NS)
    raw = re.sub(r"^@prefix[^\n]+\n", "", raw, flags=re.MULTILINE)
    raw = re.sub(
        r"^<http://www\.semanticweb\.org/spmh/ontologies/2024/3/SPMH>\s+a\s+owl:Ontology\s*;.*?^\.\s*$",
        "",
        raw,
        flags=re.MULTILINE | re.DOTALL,
    )
    raw = re.sub(
        r"^\[\]\s+a\s+owl:AllDisjointClasses\s*;.*?^\.\s*$",
        "",
        raw,
        flags=re.MULTILINE | re.DOTALL,
    )
    raw = re.sub(
        r"^(\s*:[\w]+)\s+a\s+(owl:Class|owl:ObjectProperty|owl:DatatypeProperty)\s*;",
        r"\1 rdf:type \2 ;",
        raw,
        flags=re.MULTILINE,
    )
    return raw.strip()


def public_header() -> str:
    return f"""# Public release: OOPS-clean schema + redacted A-box + HURON v1.0.4.
# Canonical: SPMH-public.owl (QASAR + OOPS!). Turtle export below.
# Namespace: {NEW_NS.rstrip('/')}

@prefix : <{NEW_NS}> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@base <{NEW_NS}> .

<{NEW_NS.rstrip("/")}> rdf:type owl:Ontology ;
    rdfs:label "Serapis Personal Mental Health Ontology (SPMH)"@en ;
    dc:title "Serapis Personal Mental Health Ontology (SPMH)" ;
    dc:description "Trace-based ontology for organizing depression-related social media evidence with provenance, aligned with DSM-5-TR diagnostic criteria."@en ;
    dc:creator "Alexandre Augusto Foppa, Wesllei Felipe Heckler, Luan Paris Feijó, Jorge Luis Victória Barbosa" ;
    dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;
    owl:versionInfo "1.0.4" .

"""


def build_public_turtle(g: Graph) -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    from annotate_huron import inject_annotations

    schema = serialize_schema_protege(g)
    schema = inject_annotations(schema)
    schema = re.sub(r"\s*owl:versionInfo\s+\"1\.0\.1\"\s*;?\s*\n", "\n", schema)
    abox = flatten_multiline_literals(load_abox_section())
    return public_header() + schema + "\n" + abox


def build_public_owl(ttl: str) -> str:
    g = Graph()
    g.parse(data=ttl, format="turtle")
    return g.serialize(format="xml")


def main() -> None:
    g = build_graph()
    ttl = build_public_turtle(g)
    owl = build_public_owl(ttl)

    OUT_TTL.write_text(ttl, encoding="utf-8")
    OUT_OWL.write_text(owl, encoding="utf-8")

    verify = Graph()
    verify.parse(OUT_TTL, format="turtle")
    verify.parse(OUT_OWL, format="xml")

    text = OUT_TTL.read_text(encoding="utf-8")
    idx = text.find("#    Individuals")
    assert idx > 0, "Individuals section missing"
    assert ":PostID01" not in text[:idx], "Instances before Individuals section"
    assert not re.search(r":isRelevant\s+(true|false)\s*\.", text), "Bare boolean isRelevant"
    assert '"""' not in text, "Multiline literals remain"
    assert text.count("owl:inverseOf") >= 6, "Missing inverse axioms"
    assert owl.startswith("<?xml"), "OWL output is not RDF/XML"

    print(f"Wrote {OUT_TTL} ({len(verify)} triples, individuals @ line {text[:idx].count(chr(10)) + 1})")
    print(f"Wrote {OUT_OWL} ({len(owl.encode())} bytes RDF/XML for OOPS! paste)")


if __name__ == "__main__":
    main()
