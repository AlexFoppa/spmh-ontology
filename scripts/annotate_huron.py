#!/usr/bin/env python3
"""Add rdfs:label and rdfs:comment for HURON/QASAR compliance."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CLASS_META: dict[str, tuple[str, str | None]] = {
    "Account": (
        "Social media account",
        "Social media account through which a person publishes posts and profiles.",
    ),
    "AlcoholUse": (
        "Alcohol use",
        "Behaviour related to alcohol consumption, relevant as a risk factor in depression assessment.",
    ),
    "Analisys": (
        "Analysis",
        "Forensic analysis procedure applied to collected digital evidence.",
    ),
    "Appetite": (
        "Appetite change",
        "Change in appetite, including loss or gain of weight, as a depression-related manifestation.",
    ),
    "Artifact": (
        "Digital artifact",
        "Preserved digital evidence gathered from social media with integrity controls.",
    ),
    "Behaviour": (
        "Behaviour",
        "Actions that may express depression, including sleep, suicidal behaviour, and substance use.",
    ),
    "Bipolar": (
        "Bipolar disorder",
        "Comorbid bipolar disorder that may require diagnostic rule-out or treatment adjustment.",
    ),
    "Birth": (
        "Birth event",
        "Birth of a child, relevant for postpartum diagnostic consideration.",
    ),
    "ChildhoodExperiences": (
        "Childhood experiences",
        "Childhood experiences, including trauma, relevant to mental health assessment.",
    ),
    "Cognition": (
        "Cognition",
        "Psychological processes in which depression may be expressed, such as memory and concentration.",
    ),
    "Collection": (
        "Collection",
        "Procedure step for collecting social media evidence.",
    ),
    "Concentration": (
        "Concentration difficulty",
        "Difficulty keeping concentration, a cognitive manifestation aligned with DSM-5-TR criteria.",
    ),
    "Condition": (
        "Condition",
        "Disease or disorder that may affect depression diagnosis or treatment planning.",
    ),
    "Context": (
        "Context",
        "Dynamic context of an individual at a specific moment, including publications or medical records.",
    ),
    "Death": (
        "Death event",
        "Death or significant loss that may explain depressed mood better than major depression.",
    ),
    "DecisionMaking": (
        "Decision-making difficulty",
        "Difficulty making decisions, a cognitive symptom associated with depression.",
    ),
    "Delusion": (
        "Delusion",
        "Less common depressive manifestation involving delusional content.",
    ),
    "DepressedMood": (
        "Depressed mood",
        None,  # keep existing rdfs:comment
    ),
    "Depression": (
        "Depression",
        "Major depressive disorder and related depression disorders represented in the ontology.",
    ),
    "Discrimination": (
        "Discrimination",
        "Experience of discrimination, including racism, as a psychosocial risk factor.",
    ),
    "Event": (
        "Event",
        "Relevant life event that may affect major depressive disorder diagnosis.",
    ),
    "Fatigue": (
        "Fatigue",
        None,  # keep existing rdfs:comment
    ),
    "Feeling": (
        "Feeling",
        "Sentiments and sensations through which depressed mood and related states may be expressed.",
    ),
    "Gastrointestinal": (
        "Gastrointestinal symptoms",
        "Gastrointestinal somatic complaints that may accompany depressive disorders.",
    ),
    "Guilt": (
        "Guilt",
        "Feelings of guilt or worthlessness associated with depressive presentations.",
    ),
    "Hypersomnia": (
        "Hypersomnia",
        "Excessive sleep, a sleep-pattern alteration relevant to depression assessment.",
    ),
    "Hypomania": (
        "Hypomanic episode",
        "Hypomanic episode used to distinguish bipolar-related presentations.",
    ),
    "Identification": (
        "Identification",
        "Procedure step for identifying and registering collected evidence.",
    ),
    "Impairment": (
        "Impairment",
        "Functional impairment caused by mental health issues across life domains.",
    ),
    "ImpulseControl": (
        "Impulse control difficulty",
        "Difficulty controlling impulses, a behavioural-cognitive manifestation.",
    ),
    "Insomnia": (
        "Insomnia",
        "Insomnia or reduced sleep, a sleep-pattern alteration relevant to depression assessment.",
    ),
    "Interest": (
        "Loss of interest",
        "Loss of interest or low energy, including anhedonia-related presentations.",
    ),
    "Irritability": (
        "Irritability",
        "Irritability or mood fluctuation that may appear in depressive disorders.",
    ),
    "Mania": (
        "Manic episode",
        "Manic episode used in differential diagnosis with bipolar disorder.",
    ),
    "MedicalRecord": (
        "Medical record",
        "Clinical record documented by mental health professionals after a session.",
    ),
    "Memory": (
        "Memory difficulty",
        "Difficulty retrieving memories, a cognitive symptom associated with depression.",
    ),
    "Pain": (
        "Pain",
        "Pain or burden feelings that may accompany depressive mood.",
    ),
    "Person": (
        "Person",
        "Individual whose social media expressions and mental-health traces are modeled.",
    ),
    "Pleasure": (
        "Diminished pleasure",
        "Diminished pleasure or loss of interest in activities.",
    ),
    "Post": (
        "Social media post",
        "Social media publication that may contain depression-related textual traces.",
    ),
    "Presentation": (
        "Presentation",
        "Procedure step for presenting processed evidence to professional review.",
    ),
    "Procedure": (
        "Procedure",
        "Technique used in the investigation cycle from collection to presentation.",
    ),
    "Profile": (
        "Social media profile",
        "Social media profile update treated as contextual evidence.",
    ),
    "PsychomotorActivity": (
        "Psychomotor activity change",
        "Change in psychomotor activity, including agitation or retardation.",
    ),
    "Psychotic": (
        "Psychotic condition",
        "Psychotic presentations that may require diagnostic differentiation.",
    ),
    "Publication": (
        "Publication",
        "Social media publication or profile update modeled as contextual evidence.",
    ),
    "Relation": (
        "Relation",
        "Affection, family, or social relation inferred from social media content.",
    ),
    "Schizophrenia": (
        "Schizophrenia",
        "Schizophrenia or related psychotic disorder considered in diagnostic rule-out.",
    ),
    "SexualAbuse": (
        "Sexual abuse",
        "History of sexual abuse relevant to mental health assessment.",
    ),
    "SignificantLoss": (
        "Significant loss",
        "Significant loss that may explain depressed mood better than major depression.",
    ),
    "Sleep": (
        "Sleep alteration",
        "Sleep-pattern alteration, including insomnia and hypersomnia.",
    ),
    "SocialIsolation": (
        "Social isolation",
        "Social isolation as a psychosocial factor in depression assessment.",
    ),
    "SomaticComplaints": (
        "Somatic complaints",
        "Somatic complaints that may accompany depressive disorders.",
    ),
    "Storage": (
        "Storage",
        "Procedure step for storing collected evidence with integrity controls.",
    ),
    "Stress": (
        "Stress",
        "Stress or distress feelings that may appear in depressive presentations.",
    ),
    "SubstanceUse": (
        "Substance use",
        "Substance abuse or related behaviour relevant to depression assessment.",
    ),
    "SuicidalBehaviour": (
        "Suicidal behaviour",
        "Suicidal ideation or suicide attempt, a significant indicator in aggravated cases.",
    ),
    "SuicideAttempt": (
        "Suicide attempt",
        "Suicide attempt as a severe behavioural indicator in depression assessment.",
    ),
    "SuicideIdeation": (
        "Suicidal ideation",
        "Suicidal ideation as a significant indicator in depression assessment.",
    ),
    "Thinking": (
        "Thinking difficulty",
        "Difficulty thinking, a cognitive manifestation associated with depression.",
    ),
    "Trace": (
        "Depression trace",
        "Clue discovered in social media content that supports professional diagnostic review.",
    ),
    "Trauma": (
        "Trauma",
        "Traumatic event relevant to mental health history and differential diagnosis.",
    ),
    "Weight": (
        "Weight change",
        "Weight gain or loss associated with appetite changes in depression.",
    ),
}

PROPERTY_META: dict[str, tuple[str, str | None]] = {
    "hasA": ("has trace", "Links a context to zero or more depression-related traces."),
    "isAbout": ("is about", "Links contextual evidence to the person under assessment."),
    "isPreservedAs": (
        "is preserved as",
        "Links a publication to the artifact that preserves its content.",
    ),
    "isResultOf": (
        "is result of",
        "Links an artifact or trace to the procedure that produced it.",
    ),
    "owns": ("owns", "Links a person to a social media account."),
    "comesFromSocialPlataform": (
        "comes from social platform",
        "Name of the social media platform that originated the account or publication.",
    ),
    "hasAge": ("has age", "Age of the person under assessment."),
    "hasCapturedMoment": (
        "has captured moment",
        "Timestamp when the evidence was captured from the platform.",
    ),
    "hasContent": ("has content", "Textual or media content associated with a context."),
    "hasEducation": ("has education", "Education level of the person under assessment."),
    "hasEpisode": (
        "has episode",
        "Flag indicating whether a condition involves episodic presentation.",
    ),
    "hasEthnicity": ("has ethnicity", "Ethnicity of the person under assessment."),
    "hasExplanation": (
        "has explanation",
        "Rationale documenting why content was classified as a depression-related trace.",
    ),
    "hasFamily": ("has family", "Family information relevant to psychosocial assessment."),
    "hasGender": ("has gender", "Gender of the person under assessment."),
    "hasHashcode": (
        "has hashcode",
        "Cryptographic hash ensuring integrity of preserved artifact content.",
    ),
    "hasImageContent": ("has image content", "Image content associated with a context."),
    "hasIncome": ("has income", "Income information relevant to psychosocial assessment."),
    "hasMoment": (
        "has moment",
        "Timestamp when the publication or record was created.",
    ),
    "hasName": ("has name", "Name of the person under assessment."),
    "hasRelationship": (
        "has relationship",
        "Relationship information relevant to psychosocial assessment.",
    ),
    "hasSentimentScore": (
        "has sentiment score",
        "Sentiment score calculated by a sentiment analysis technique such as VADER.",
    ),
    "hasTextContent": ("has text content", "Textual content associated with a context."),
    "hasUrl": ("has URL", "URL of an account, publication, or preserved artifact."),
    "hasVideoContent": ("has video content", "Video content associated with a context."),
    "isRelevant": (
        "is relevant",
        "Flag indicating whether a publication is relevant to depression assessment.",
    ),
}

ENTITY_START = re.compile(
    r"^:(\w+)\s+(?:rdf:type|a)\s+owl:(Class|ObjectProperty|DatatypeProperty)\s*([;.])"
)
META = {**CLASS_META, **PROPERTY_META}


def inject_annotations(text: str) -> str:
    text = text.replace(
        'rdfs:comment "An artifcat is the result of a procedure"',
        'rdfs:comment "An artifact is the result of a procedure"',
    )
    text = text.replace(
        'rdfs:comment "A sentiment socre calculated by sentiment analysis techniques"',
        'rdfs:comment "A sentiment score calculated by sentiment analysis techniques"',
    )
    text = text.replace('owl:versionInfo "1.0.0"', 'owl:versionInfo "1.0.1"')

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = ENTITY_START.match(line)
        if not match:
            out.append(line)
            i += 1
            continue

        name, _kind, terminator = match.groups()
        block = [line]
        i += 1
        if terminator == ".":
            block_end = 0
        else:
            while i < len(lines):
                block.append(lines[i])
                if re.search(r"\.\s*$", lines[i]):
                    break
                i += 1
            block_end = len(block) - 1

        label, comment = META.get(name, (None, None))
        if label:
            block_text = "".join(block)
            insert_lines: list[str] = []
            if "rdfs:label" not in block_text:
                insert_lines.append(f'    rdfs:label "{label}"@en ;\n')
            if comment and "rdfs:comment" not in block_text:
                insert_lines.append(f'    rdfs:comment "{comment}"@en ;\n')

            if insert_lines:
                if terminator == ".":
                    block[0] = block[0].rstrip().rstrip(".") + " ;\n"
                    block.extend(insert_lines)
                    block.append(" .\n")
                else:
                    block.insert(1, "".join(insert_lines))

        out.extend(block)
        i += 1

    result = "".join(out)
    result = re.sub(r";\s*\n(\s*\.)", r"\n\1", result)
    return result


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]] or [
        Path(__file__).resolve().parents[1] / "SPMH-public.ttl",
    ]
    for path in paths:
        updated = inject_annotations(path.read_text(encoding="utf-8"))
        path.write_text(updated, encoding="utf-8")
        labels = updated.count("rdfs:label")
        comments = updated.count("rdfs:comment")
        print(f"{path}: rdfs:label={labels}, rdfs:comment={comments}")


if __name__ == "__main__":
    main()
