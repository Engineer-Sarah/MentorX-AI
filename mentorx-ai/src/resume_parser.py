"""
resume_parser.py – Simple resume text extraction and section splitting.
Used by the Resume Analyzer to pre-process pasted text.
"""

import re


# Common section headings found in resumes
SECTION_PATTERNS = [
    "summary", "objective", "profile", "about",
    "experience", "work experience", "professional experience", "employment",
    "education", "academic", "qualifications",
    "skills", "technical skills", "core competencies", "competencies",
    "projects", "portfolio",
    "certifications", "certificates", "licenses",
    "achievements", "awards", "honours",
    "languages", "interests", "hobbies",
    "references",
]


def clean_text(text: str) -> str:
    """Basic text cleaning: normalise whitespace, strip control chars."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sections(text: str) -> dict[str, str]:
    """
    Attempt to split a resume into named sections.

    Returns a dict mapping section_name -> section_text.
    If sections cannot be detected, returns {"full_text": text}.
    """
    sections: dict[str, str] = {}
    lines = text.split("\n")

    current_section = "header"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip().lower().rstrip(":")

        # Check if this line matches a known section heading
        matched_section = None
        for pattern in SECTION_PATTERNS:
            if stripped == pattern or stripped.startswith(pattern + " "):
                matched_section = pattern.title()
                break

        # Also detect ALL-CAPS short lines as headings
        if not matched_section and line.strip().isupper() and len(line.strip()) < 50:
            matched_section = line.strip().title()

        if matched_section:
            # Save previous section
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = matched_section
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    # Fallback: if only one section, return as full_text
    if len(sections) <= 1:
        return {"full_text": text}

    return sections


def estimate_word_count(text: str) -> int:
    """Rough word count."""
    return len(text.split())


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from resume text."""
    return re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from resume text."""
    return re.findall(r"https?://\S+", text)


def get_resume_stats(text: str) -> dict:
    """Compute basic statistics about the resume."""
    sections = split_sections(text)
    return {
        "word_count": estimate_word_count(text),
        "section_count": len(sections),
        "sections_detected": list(sections.keys()),
        "emails": extract_emails(text),
        "urls": extract_urls(text),
    }
