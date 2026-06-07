"""Area & paper-type classification by keyword matching.

Deterministic and offline. Matches the manuscript text against the research-area
keyword families from CLAUDE.md. Never invents an area; if nothing matches it
reports ``UNKNOWN`` / ``NEEDS_USER_INPUT``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# area_key -> (human label, venue_family codes, keywords)
AREA_KEYWORDS: dict[str, dict] = {
    "cloud_systems_architecture": {
        "label": "Cloud, systems & computer architecture",
        "families": [1],
        "keywords": [
            "computer architecture", "high-performance computing", "hpc",
            "distributed systems", "cloud computing", "edge computing",
            "serverless", "kubernetes", "orchestration", "cloudsim",
            "task scheduling", "resource allocation", "load balancing",
            "scheduling", "starvation", "weighted fair queuing", "datacenter",
            "energy-aware", "green computing", "risc-v", "heterogeneous architectures",
        ],
    },
    "ml_cv_robust": {
        "label": "Machine learning, computer vision & robust generalization",
        "families": [2, 3, 12],
        "keywords": [
            "machine learning", "deep learning", "computer vision",
            "transfer learning", "domain adaptation", "domain generalization",
            "out-of-distribution", "covariate shift", "concept shift",
            "calibration transfer", "cross-validation", "leakage-free",
            "benchmark design", "robust evaluation", "explainable ai", "interpretable",
        ],
    },
    "fas_biometrics_security": {
        "label": "Face anti-spoofing, biometrics & security",
        "families": [4],
        "keywords": [
            "face anti-spoofing", "anti-spoofing", "presentation attack",
            "biometric", "face recognition", "spoofing", "replay attack",
            "print attack", "deepfake", "3d convolutional", "spatiotemporal",
            "apcer", "bpcer", "acer", "pad",
        ],
    },
    "document_ai_htr": {
        "label": "HTR, OCR & Document AI",
        "families": [5],
        "keywords": [
            "handwritten text recognition", "htr", "ocr", "document analysis",
            "document ai", "handwriting", "offline handwriting", "low-resource",
            "catalan htr", "multilingual htr", "synthetic handwriting",
            "writer-independent", "transformer-based htr", "cer", "wer",
        ],
    },
    "education": {
        "label": "Education & computing education",
        "families": [6, 7, 8],
        "keywords": [
            "educational technology", "computing education", "cs education",
            "programming education", "cs1", "k-12", "k–12", "stem education",
            "engineering education", "computational thinking", "pseudocode",
            "block-based", "curriculum", "cs2023", "prisma", "systematic review",
        ],
    },
    "agri_food_spectral": {
        "label": "Agricultural AI, hyperspectral imaging & food safety",
        "families": [9, 10, 11],
        "keywords": [
            "agricultural ai", "precision agriculture", "wheat", "food safety",
            "food quality", "mycotoxin", "deoxynivalenol", "don screening",
            "fusarium", "near-infrared", "nir-hsi", "hyperspectral", "spectroscopy",
            "chemometrics", "single-kernel", "non-destructive", "remote sensing",
            "batch effect", "acquisition-session",
        ],
    },
    "dataset_benchmark": {
        "label": "Dataset, benchmark & software papers",
        "families": [13, 14],
        "keywords": [
            "data descriptor", "dataset paper", "benchmark", "corpus",
            "software paper", "reproducibility", "resource paper", "open science",
            "fair data", "evaluation protocol",
        ],
    },
}

# paper_type heuristics (keyword -> paper_type).
PAPER_TYPE_HINTS = [
    (["systematic review", "prisma"], "systematic review"),
    (["survey"], "survey"),
    (["data descriptor", "dataset paper", "we release", "we introduce a dataset"], "data descriptor"),
    (["benchmark"], "benchmark paper"),
    (["software", "toolkit", "library", "we present a tool"], "software article"),
    (["scheduler", "architecture", "system design", "deployment"], "systems paper"),
]


@dataclass
class Classification:
    detected_areas: list[str] = field(default_factory=list)
    detected_area_labels: list[str] = field(default_factory=list)
    paper_type: str = "UNKNOWN"
    likely_venue_families: list[int] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "detected_areas": self.detected_areas,
            "detected_area_labels": self.detected_area_labels,
            "paper_type": self.paper_type,
            "likely_venue_families": self.likely_venue_families,
            "scores": self.scores,
        }


def classify_text(text: str) -> Classification:
    low = (text or "").lower()
    scores: dict[str, int] = {}
    families: set[int] = set()

    for area_key, spec in AREA_KEYWORDS.items():
        count = 0
        for kw in spec["keywords"]:
            count += len(re.findall(re.escape(kw), low))
        if count > 0:
            scores[area_key] = count
            families.update(spec["families"])

    detected = sorted(scores, key=lambda k: scores[k], reverse=True)
    labels = [AREA_KEYWORDS[k]["label"] for k in detected]

    paper_type = "UNKNOWN"
    for hints, ptype in PAPER_TYPE_HINTS:
        if any(h in low for h in hints):
            paper_type = ptype
            break
    if paper_type == "UNKNOWN" and detected:
        paper_type = "research article"

    return Classification(
        detected_areas=detected,
        detected_area_labels=labels,
        paper_type=paper_type,
        likely_venue_families=sorted(families),
        scores=scores,
    )
