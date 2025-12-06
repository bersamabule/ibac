"""
Knowledge Base Loader

Loads markdown modules from the KNOWLEDGE_BASE directory and assembles
them into context for the assessment engine.

Also loads calibration anchors from IBAC_Calibration_Package for the
forced-comparison assessment architecture.
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Knowledge base path - use KNOWLEDGE_BASE (uppercase) as that's the actual folder name
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "KNOWLEDGE_BASE"

# Calibration package path
CALIBRATION_PATH = Path(__file__).parent.parent / "IBAC_Calibration_Package"

# Log path information on module load
logger.info(f"knowledge_base.py __file__: {__file__}")
logger.info(f"KNOWLEDGE_BASE_PATH: {KNOWLEDGE_BASE_PATH}")
logger.info(f"KNOWLEDGE_BASE_PATH resolved: {KNOWLEDGE_BASE_PATH.resolve()}")
logger.info(f"KNOWLEDGE_BASE_PATH exists: {KNOWLEDGE_BASE_PATH.exists()}")
logger.info(f"CALIBRATION_PATH: {CALIBRATION_PATH}")
logger.info(f"CALIBRATION_PATH resolved: {CALIBRATION_PATH.resolve()}")
logger.info(f"CALIBRATION_PATH exists: {CALIBRATION_PATH.exists()}")

# Also print to stdout for Railway logs
print(f"[knowledge_base] __file__: {__file__}")
print(f"[knowledge_base] KNOWLEDGE_BASE_PATH: {KNOWLEDGE_BASE_PATH} (exists: {KNOWLEDGE_BASE_PATH.exists()})")
print(f"[knowledge_base] CALIBRATION_PATH: {CALIBRATION_PATH} (exists: {CALIBRATION_PATH.exists()})")


def load_module(relative_path: str) -> str:
    """Load a single markdown module."""
    full_path = KNOWLEDGE_BASE_PATH / relative_path
    if full_path.exists():
        return full_path.read_text(encoding='utf-8')
    return ""


def load_system_prompt() -> str:
    """Load the core system prompt."""
    return load_module("00_SYSTEM_PROMPT.md")


def load_criterion_modules(criteria: list[str]) -> str:
    """
    Load modules for specified criteria.

    Args:
        criteria: List of criterion letters, e.g., ["A", "B"]

    Returns:
        Combined content of all relevant modules
    """
    content_parts = []

    criterion_map = {
        "A": "01_CRITERION_A_ANALYSING",
        "B": "02_CRITERION_B_ORGANIZING",
        "C": "03_CRITERION_C_PRODUCING",
        "D": "04_CRITERION_D_LANGUAGE"
    }

    for criterion in criteria:
        folder = criterion_map.get(criterion.upper())
        if folder:
            folder_path = KNOWLEDGE_BASE_PATH / folder
            if folder_path.exists():
                for md_file in sorted(folder_path.glob("*.md")):
                    content_parts.append(f"## {md_file.stem}\n\n{md_file.read_text(encoding='utf-8')}")

    return "\n\n---\n\n".join(content_parts)


def load_cross_criteria() -> str:
    """Load cross-criteria modules (archetypes, compensation rules, etc.)."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "05_CROSS_CRITERIA"

    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))

    return "\n\n---\n\n".join(content_parts)


def load_assessment_protocols() -> str:
    """Load assessment protocol modules."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "06_ASSESSMENT_PROTOCOLS"

    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))

    return "\n\n---\n\n".join(content_parts)


def load_diagnostic_tools() -> str:
    """Load diagnostic tool modules."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "07_DIAGNOSTIC_TOOLS"

    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))

    return "\n\n---\n\n".join(content_parts)


def assemble_assessment_context(criteria: list[str]) -> str:
    """
    Assemble the full knowledge base context for an assessment.

    Args:
        criteria: List of criteria being assessed, e.g., ["A"] or ["A", "B"]

    Returns:
        Complete context string to include in the API prompt
    """
    parts = [
        "# IB MYP Assessment Expert System Knowledge Base\n",
        load_system_prompt(),
        "\n\n# Criterion-Specific Frameworks\n",
        load_criterion_modules(criteria),
        "\n\n# Cross-Criteria Frameworks\n",
        load_cross_criteria(),
        "\n\n# Assessment Protocols\n",
        load_assessment_protocols(),
        "\n\n# Diagnostic Tools\n",
        load_diagnostic_tools()
    ]

    return "\n".join(parts)


def get_knowledge_base_version() -> str:
    """Return the current knowledge base version."""
    return "2.0"


# ============== Calibration Anchor Loading ==============

def load_calibration_anchors(criteria: list[str]) -> str:
    """
    Load calibration anchor files for specified criteria.

    Args:
        criteria: List of criterion letters, e.g., ["A", "B", "C", "D"]

    Returns:
        Combined content of calibration modules as a string
    """
    content_parts = []
    calibration_dir = CALIBRATION_PATH / "calibration_modules"

    # Map criteria to their calibration files
    criterion_files = {
        "A": "CALIBRATION_A_ANALYSING.md",
        "B": "CALIBRATION_B_ORGANIZING.md",
        "C": "CALIBRATION_C_PRODUCING_TEXT.md",
        "D": "CALIBRATION_D_USING_LANGUAGE.md"
    }

    # Load each criterion's calibration anchors
    for criterion in criteria:
        criterion_upper = criterion.upper()
        if criterion_upper in criterion_files:
            file_path = calibration_dir / criterion_files[criterion_upper]
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                content_parts.append(f"# Calibration Anchors for Criterion {criterion_upper}\n\n{content}")

    # For multi-criterion assessments, also load cross-criteria calibration
    if len(criteria) > 1:
        cross_criteria_path = calibration_dir / "CALIBRATION_CROSS_CRITERIA.md"
        if cross_criteria_path.exists():
            content = cross_criteria_path.read_text(encoding='utf-8')
            content_parts.append(f"# Cross-Criteria Calibration\n\n{content}")

    return "\n\n---\n\n".join(content_parts)


def load_cross_criteria_profiles() -> list[dict]:
    """
    Load the cross-criteria diagnostic profiles from JSON.

    Returns:
        List of profile dictionaries containing name, pattern, student_work, diagnosis, etc.
    """
    profiles_path = CALIBRATION_PATH / "cross_criteria_profiles.json"
    if profiles_path.exists():
        content = profiles_path.read_text(encoding='utf-8')
        return json.loads(content)
    return []


def format_cross_criteria_profiles_for_prompt() -> str:
    """
    Format cross-criteria profiles for inclusion in the assessment prompt.

    Returns:
        Formatted string describing all diagnostic profiles
    """
    profiles = load_cross_criteria_profiles()
    if not profiles:
        return ""

    parts = ["# CROSS-CRITERIA DIAGNOSTIC PROFILES\n"]
    parts.append("Use these profiles to detect uneven performance patterns. Students rarely perform uniformly across all criteria.\n")

    for i, profile in enumerate(profiles, 1):
        parts.append(f"\n## Profile {i}: {profile['name']}\n")
        parts.append(f"**Pattern:** {profile['pattern']}\n")
        parts.append(f"**Pathology:** {profile.get('pathology', '')}\n")
        parts.append(f"**Instructional Priority:** {profile.get('instructional_priority', '')}\n")

        # Include diagnosis summary
        if 'diagnosis' in profile:
            parts.append("\n**Expected Scores:**\n")
            for crit, desc in profile['diagnosis'].items():
                parts.append(f"- Criterion {crit}: {desc}\n")

    return "".join(parts)
