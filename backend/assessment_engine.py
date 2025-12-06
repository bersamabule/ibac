"""
Assessment Engine

Generates IB MYP assessments using Claude API and the knowledge base.

v2.0: Updated to use forced-comparison architecture with calibration anchors.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from .knowledge_base import (
    assemble_assessment_context,
    get_knowledge_base_version,
    load_calibration_anchors,
    format_cross_criteria_profiles_for_prompt
)

load_dotenv(override=True)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ============== System Context ==============

SYSTEM_CONTEXT = """You are an IB MYP Language and Literature assessment expert calibrated against standardized student work samples. Your task is to assess student work by EXPLICIT COMPARISON to reference samples, not by abstract evaluation.

CRITICAL PRINCIPLES:
1. Assessment is COMPARATIVE — every score must reference a calibration anchor
2. Students RARELY perform uniformly — identical scores across criteria are suspicious
3. Evidence must come from BOTH the student's work AND the reference samples
4. You must DETECT uneven profiles (e.g., "Brilliant Mess": High A, Low B)

LEVEL DISTRIBUTION REALITY (middle school):
- Level 7-8: Exceptional (5-15% of students)
- Level 5-6: Above average (25-35%)
- Level 3-4: Typical majority (40-50%)
- Level 1-2: Struggling (10-20%)

Level 4 is NOT the default. It must be earned through demonstrated "adequate" performance.
"""

# ============== Forced Comparison Instructions ==============

FORCED_COMPARISON_INSTRUCTIONS = """
══════════════════════════════════════════════════════════════
ASSESSMENT PROTOCOL: FORCED COMPARISON METHOD
══════════════════════════════════════════════════════════════

You MUST complete the following steps IN ORDER for each criterion:

### STEP 1: Compare to Level 1-2 Reference

Read the Level 1-2 reference sample again. Then answer:
- Is the student's work MORE sophisticated than this reference?
- What SPECIFIC features in the student's work exceed the reference?
- What features (if any) are at the SAME level as the reference?

Cite at least ONE quote from the student and ONE from the reference.

### STEP 2: Compare to Level 3-4 Reference

Read the Level 3-4 reference sample. Then answer:
- Does the student's work match or exceed "adequate" performance?
- What SPECIFIC features demonstrate adequacy (or lack thereof)?
- Is the student formulaic like the reference, or going beyond?

Cite evidence from both texts.

### STEP 3: Compare to Level 5-6 Reference

Read the Level 5-6 reference sample. Then answer:
- Does the student demonstrate SYNTHESIS (multiple elements working together)?
- Is there evidence of going beyond formulaic response?
- What SPECIFIC features show substantial engagement (or its absence)?

Cite evidence from both texts.

### STEP 4: Compare to Level 7-8 Reference

Read the Level 7-8 reference sample. Then answer:
- Is there META-COGNITIVE awareness or philosophical depth?
- Does the student take RISKS that pay off?
- What would need to change for this work to reach Level 7-8?

### STEP 5: Assign Level with Justification

Based on your comparisons:
- Which reference sample does the student's work MOST closely resemble?
- What is the precise level (1-8)?
- What 2-3 key features justify this level?

══════════════════════════════════════════════════════════════
"""

# ============== Output Format ==============

OUTPUT_FORMAT = """
══════════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT
══════════════════════════════════════════════════════════════

Respond with a JSON object. Do NOT include any text before or after the JSON.

{{
  "profile_detection": {{
    "detected_profile": "Name of profile if detected (e.g., 'Unbound Architect') or 'None - uniform performance'",
    "confidence": "high/medium/low",
    "reasoning": "Brief explanation of why this profile fits or why scores are uniform"
  }},

  "overall_summary": "2-3 sentence holistic summary acknowledging the profile pattern",

  "criterion_assessments": [
    {{
      "criterion": "A",
      "level": <number 1-8>,

      "comparison_analysis": {{
        "vs_level_1_2": "Student is [MORE/LESS/SIMILAR] sophisticated because [evidence]",
        "vs_level_3_4": "Student [EXCEEDS/MATCHES/FALLS SHORT OF] adequate because [evidence]",
        "vs_level_5_6": "Student [DEMONSTRATES/LACKS] synthesis because [evidence]",
        "vs_level_7_8": "Student [SHOWS/LACKS] meta-cognitive depth because [evidence]"
      }},

      "closest_reference": "Sample ID (e.g., 'A-05') that most closely matches",

      "level_rationale": "3-4 sentences explaining why this specific level, with quotes from student work",

      "evidence_quotes": [
        {{"quote": "exact quote from student", "demonstrates": "what this shows"}},
        {{"quote": "exact quote from student", "demonstrates": "what this shows"}}
      ],

      "strand_performance": {{
        "strand_i": "limited/adequate/substantial/excellent",
        "strand_ii": "limited/adequate/substantial/excellent",
        "strand_iii": "limited/adequate/substantial/excellent"
      }},

      "diagnostic_notes": "Additional observations about this criterion"
    }}
  ],

  "identified_strengths": ["strength 1", "strength 2", "strength 3"],

  "growth_areas": ["area 1", "area 2"],

  "instructional_priority": "The single most important next step for this student"
}}

══════════════════════════════════════════════════════════════
FINAL VERIFICATION
══════════════════════════════════════════════════════════════

Before submitting, verify:
- Did I compare to ALL FOUR reference levels for each criterion?
- Did I cite specific evidence from the student's work?
- Are my scores genuinely different across criteria, or have I flattened?
- If scores are uniform, have I verified this matches "Checkbox Champion" profile?
- Did I identify the closest reference sample for each criterion?

Now generate the assessment JSON:
"""


def generate_assessment(
    assignment_title: str,
    task_type: str,
    prompt_text: str,
    criteria_assessed: list[str],
    student_name: str,
    grade_level: int,
    submitted_text: str,
    word_count: int
) -> dict:
    """
    Generate an IB MYP assessment for a student submission using forced-comparison architecture.

    Returns:
        dict: The parsed assessment data with profile detection and comparison analysis

    Raises:
        ValueError: If the API response cannot be parsed as valid JSON
    """

    # Format the criteria list
    criteria_list = ", ".join([f"Criterion {c}" for c in criteria_assessed])

    # Build the full prompt with all components
    prompt_parts = []

    # 1. System Context
    prompt_parts.append(SYSTEM_CONTEXT)

    # 2. Calibration Anchors (per-criterion reference samples)
    calibration_anchors = load_calibration_anchors(criteria_assessed)
    if calibration_anchors:
        prompt_parts.append("\n\n" + "=" * 60)
        prompt_parts.append("CALIBRATION ANCHORS - REFERENCE SAMPLES")
        prompt_parts.append("=" * 60 + "\n")
        prompt_parts.append(calibration_anchors)

    # 3. Cross-Criteria Profiles
    cross_criteria_profiles = format_cross_criteria_profiles_for_prompt()
    if cross_criteria_profiles:
        prompt_parts.append("\n\n" + "=" * 60)
        prompt_parts.append(cross_criteria_profiles)

    # 4. Student Submission
    prompt_parts.append("\n\n" + "=" * 60)
    prompt_parts.append("STUDENT SUBMISSION FOR ASSESSMENT")
    prompt_parts.append("=" * 60 + "\n")
    prompt_parts.append(f"""
**Student:** {student_name}
**Grade Level:** {grade_level}
**Assignment:** {assignment_title}
**Task Type:** {task_type}

**Prompt Given to Student:**
{prompt_text}

**Criteria to Assess:** {criteria_list}

**Student Work ({word_count} words):**

{submitted_text}
""")

    # 5. Forced Comparison Instructions
    prompt_parts.append(FORCED_COMPARISON_INSTRUCTIONS)

    # 6. Output Format
    prompt_parts.append(OUTPUT_FORMAT)

    # Combine all parts
    full_prompt = "\n".join(prompt_parts)

    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    )

    # Extract the response text
    response_text = message.content[0].text.strip()

    # Parse JSON from response
    # Handle case where response might have markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.startswith("```json") or line.startswith("```"):
                if not in_json and "json" in line:
                    in_json = True
                    continue
                elif in_json:
                    in_json = False
                    continue
                else:
                    in_json = True
                    continue
            elif in_json:
                json_lines.append(line)
        response_text = "\n".join(json_lines)

    try:
        assessment_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse assessment response as JSON: {e}\n\nResponse was:\n{response_text}")

    # Add knowledge base version to the response
    assessment_data["knowledge_base_version"] = get_knowledge_base_version()

    # Transform the new format to be compatible with existing database structure
    # while preserving the new fields
    transformed_data = transform_assessment_response(assessment_data)

    return transformed_data


def transform_assessment_response(assessment_data: dict) -> dict:
    """
    Transform the new v2 assessment format to include both old and new fields.

    This ensures backward compatibility with the database while adding new
    profile_detection and comparison_analysis fields.
    """
    result = {
        "knowledge_base_version": assessment_data.get("knowledge_base_version", "2.0"),
        "overall_summary": assessment_data.get("overall_summary", ""),
        "identified_strengths": "; ".join(assessment_data.get("identified_strengths", [])),
        "growth_areas": "; ".join(assessment_data.get("growth_areas", [])),
        "instructional_priority": assessment_data.get("instructional_priority", ""),
    }

    # Handle profile detection
    profile = assessment_data.get("profile_detection", {})
    result["archetype_primary"] = profile.get("detected_profile", "Not detected")
    result["archetype_notes"] = f"Confidence: {profile.get('confidence', 'unknown')}. {profile.get('reasoning', '')}"

    # Store full profile detection as JSON for the new field
    result["profile_detection"] = profile

    # Transform criterion assessments
    criterion_scores = []
    for crit_assessment in assessment_data.get("criterion_assessments", []):
        score = {
            "criterion": crit_assessment.get("criterion", ""),
            "level": crit_assessment.get("level", 0),
            "level_rationale": crit_assessment.get("level_rationale", ""),
            "diagnostic_notes": crit_assessment.get("diagnostic_notes", ""),
        }

        # Transform evidence quotes
        evidence = crit_assessment.get("evidence_quotes", [])
        score["evidence_quotes"] = [
            {
                "quote": eq.get("quote", ""),
                "analysis": eq.get("demonstrates", "")
            }
            for eq in evidence
        ]

        # Transform strand performance to match old format
        strand_perf = crit_assessment.get("strand_performance", {})
        score["strand_scores"] = {
            "strand_i": {
                "performance": strand_perf.get("strand_i", "not assessed"),
                "descriptor": get_strand_descriptor(crit_assessment.get("criterion", ""), "i"),
                "notes": ""
            },
            "strand_ii": {
                "performance": strand_perf.get("strand_ii", "not assessed"),
                "descriptor": get_strand_descriptor(crit_assessment.get("criterion", ""), "ii"),
                "notes": ""
            },
            "strand_iii": {
                "performance": strand_perf.get("strand_iii", "not assessed"),
                "descriptor": get_strand_descriptor(crit_assessment.get("criterion", ""), "iii"),
                "notes": ""
            }
        }

        # Add new comparison analysis fields
        score["comparison_analysis"] = crit_assessment.get("comparison_analysis", {})
        score["closest_reference"] = crit_assessment.get("closest_reference", "")

        criterion_scores.append(score)

    result["criterion_scores"] = criterion_scores

    return result


def get_strand_descriptor(criterion: str, strand: str) -> str:
    """Get the descriptor for a specific strand of a criterion."""
    descriptors = {
        "A": {
            "i": "identify and explain content, context, language, structure, technique, style",
            "ii": "identify and explain effects of creator's choices on audience",
            "iii": "justify opinions and ideas using examples, explanations, terminology",
            "iv": "evaluate similarities and differences between texts"
        },
        "B": {
            "i": "employ organizational structures appropriate to context",
            "ii": "organize opinions and ideas logically and coherently",
            "iii": "use referencing and formatting tools appropriately"
        },
        "C": {
            "i": "produce texts that demonstrate insight, imagination, and sensitivity",
            "ii": "make stylistic choices for impact on audience",
            "iii": "select relevant details and examples to develop ideas"
        },
        "D": {
            "i": "use appropriate and varied vocabulary, sentence structures, forms of expression",
            "ii": "write and speak in a register and style appropriate to context",
            "iii": "use correct grammar, syntax, punctuation, spelling, conventions"
        }
    }
    return descriptors.get(criterion.upper(), {}).get(strand, "")
