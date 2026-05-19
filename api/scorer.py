"""
api/scorer.py — ATS scoring engine simulating 2005-era dumb ATS machines.

- score_resume(extraction: dict) -> dict: Compute full ATS compatibility score.
  Returns comprehensive scoring breakdown with issues and suggestions.

Scoring philosophy: 2005-era ATS systems were pure text parsers.
They couldn't read: images, columns, tables, text boxes, headers/footers,
fancy fonts, special chars, PDFs with embedded graphics. They parsed top-to-bottom,
left-to-right plain text. Keywords had to be exact matches.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# --- SECTION PATTERNS ---
SECTION_HEADERS = {
    "contact": [
        r'\b(contact|phone|email|address|linkedin|github|portfolio|website|mobile|tel)\b',
        r'\b\d{3}[\s\-\.]\d{3}[\s\-\.]\d{4}\b',  # phone
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
    ],
    "summary": [
        r'\b(summary|objective|profile|about|overview|professional summary|career objective)\b',
    ],
    "experience": [
        r'\b(experience|work experience|employment|work history|professional experience|career history|positions)\b',
    ],
    "education": [
        r'\b(education|academic|degree|university|college|school|gpa|bachelor|master|phd|diploma|certification|graduated)\b',
    ],
    "skills": [
        r'\b(skills|technical skills|core competencies|competencies|technologies|tools|expertise|proficiencies)\b',
    ],
    "projects": [
        r'\b(projects|portfolio|contributions|open source|personal projects)\b',
    ],
    "awards": [
        r'\b(awards|honors|achievements|recognition|accomplishments)\b',
    ],
    "publications": [
        r'\b(publications|papers|research|articles|journals)\b',
    ],
    "languages": [
        r'\b(languages|language skills|spoken languages)\b',
    ],
    "certifications": [
        r'\b(certifications|licenses|certificates|credentials|courses)\b',
    ],
    "volunteer": [
        r'\b(volunteer|volunteering|community|civic|nonprofit)\b',
    ],
}

# Characters that 2005 ATS systems choked on
PROBLEMATIC_CHARS = {
    '\u2022': 'bullet •',
    '\u2019': "smart apostrophe '",
    '\u2018': "smart apostrophe '",
    '\u201c': 'smart quote "',
    '\u201d': 'smart quote "',
    '\u2013': 'en-dash –',
    '\u2014': 'em-dash —',
    '\u00a0': 'non-breaking space',
    '\u200b': 'zero-width space',
    '\u2026': 'ellipsis …',
    '\ufffd': 'replacement character (unreadable)',
}

# Fonts that old ATS systems handled poorly
BAD_FONTS = [
    'symbol', 'wingdings', 'webdings', 'dingbats', 'zapfdingbats',
    'marlett', 'ornament', 'decorative',
]

FANCY_FONTS = [
    'times', 'garamond', 'palatino', 'baskerville', 'bookman',
    'caslon', 'didot', 'bodoni', 'futura', 'gill sans',
]

SAFE_FONTS = [
    'arial', 'helvetica', 'verdana', 'tahoma', 'trebuchet',
    'calibri', 'cambria', 'georgia', 'courier', 'times new roman',
]


def score_resume(extraction: dict[str, Any]) -> dict[str, Any]:
    """
    Main scoring function. Takes extraction dict, returns full score report.
    """
    raw_text = extraction.get("raw_text", "")
    text_lower = raw_text.lower()

    issues = []
    suggestions = []

    # --- 1. READABILITY SCORE (can the ATS physically extract the text?) ---
    readability_score = 100
    readability_breakdown = {}

    # Text extraction quality
    word_count = extraction.get("word_count", 0)
    char_count = extraction.get("char_count", 0)

    if word_count < 50:
        penalty = 40
        readability_score -= penalty
        readability_breakdown["too_little_text"] = -penalty
        issues.append({
            "severity": "critical",
            "category": "readability",
            "title": "Almost no text extracted",
            "detail": f"Only {word_count} words could be read. The ATS likely sees a near-blank document — most content may be in images or unreadable format.",
            "points_lost": penalty,
        })
    elif word_count < 150:
        penalty = 20
        readability_score -= penalty
        readability_breakdown["low_text"] = -penalty
        issues.append({
            "severity": "high",
            "category": "readability",
            "title": "Low word count extracted",
            "detail": f"Only {word_count} words extracted. ATS systems need enough text to parse sections and keywords.",
            "points_lost": penalty,
        })

    # Encoding issues
    encoding_issues = extraction.get("encoding_issues", [])
    if encoding_issues:
        penalty = min(15, len(encoding_issues) * 5)
        readability_score -= penalty
        readability_breakdown["encoding_issues"] = -penalty
        for ei in encoding_issues:
            issues.append({
                "severity": "medium",
                "category": "readability",
                "title": "Encoding issue detected",
                "detail": ei,
                "points_lost": round(penalty / len(encoding_issues)),
            })

    # Problematic characters
    found_bad_chars = {}
    for char, name in PROBLEMATIC_CHARS.items():
        count = raw_text.count(char)
        if count > 0:
            found_bad_chars[name] = count

    if found_bad_chars:
        penalty = min(12, len(found_bad_chars) * 3)
        readability_score -= penalty
        readability_breakdown["special_chars"] = -penalty
        char_list = ", ".join([f"{n} ({c}x)" for n, c in list(found_bad_chars.items())[:5]])
        issues.append({
            "severity": "medium",
            "category": "readability",
            "title": "Special characters detected",
            "detail": f"Found: {char_list}. Old ATS systems convert these to garbage characters or skip them entirely.",
            "points_lost": penalty,
        })
        suggestions.append("Replace smart quotes, em-dashes, and bullet symbols with plain ASCII equivalents (straight quotes, hyphens, plain asterisks or dashes for bullets).")

    # Non-text ratio (images, graphics)
    non_text_ratio = extraction.get("non_text_ratio", 0.0)
    if non_text_ratio > 0.5:
        penalty = 25
        readability_score -= penalty
        readability_breakdown["heavy_graphics"] = -penalty
        issues.append({
            "severity": "critical",
            "category": "readability",
            "title": "Heavy use of images/graphics",
            "detail": f"Approximately {round(non_text_ratio * 100)}% of the document appears to be non-text. ATS systems cannot read images — any text embedded in graphics is invisible.",
            "points_lost": penalty,
        })
        suggestions.append("Remove graphic elements, profile photos, skill bars, icons, and any infographic sections. Pure text only.")
    elif non_text_ratio > 0.25:
        penalty = 10
        readability_score -= penalty
        readability_breakdown["moderate_graphics"] = -penalty
        issues.append({
            "severity": "medium",
            "category": "readability",
            "title": "Significant graphic content detected",
            "detail": "Document contains notable image/graphic content. ATS parsers skip these entirely.",
            "points_lost": penalty,
        })

    has_images = extraction.get("has_images", False)
    if has_images and non_text_ratio <= 0.25:
        penalty = 5
        readability_score -= penalty
        readability_breakdown["has_images"] = -penalty
        issues.append({
            "severity": "low",
            "category": "readability",
            "title": "Images present",
            "detail": "Images found in document. ATS systems ignore all image content including embedded text, photos, and icons.",
            "points_lost": penalty,
        })

    # Font analysis
    fonts_used = [f.lower() for f in extraction.get("fonts_used", [])]
    bad_fonts_found = [f for f in fonts_used if any(b in f for b in BAD_FONTS)]
    if bad_fonts_found:
        penalty = 15
        readability_score -= penalty
        readability_breakdown["bad_fonts"] = -penalty
        issues.append({
            "severity": "high",
            "category": "readability",
            "title": f"Incompatible font(s): {', '.join(bad_fonts_found[:3])}",
            "detail": "Symbol/Wingdings/decorative fonts render as garbage in ATS parsers. Any text in these fonts becomes unreadable gibberish.",
            "points_lost": penalty,
        })
        suggestions.append(f"Replace {', '.join(bad_fonts_found)} with Arial, Calibri, or Times New Roman.")

    readability_score = max(0, readability_score)

    # --- 2. ATS FRIENDLINESS SCORE (can the ATS make sense of the structure?) ---
    ats_score = 100
    ats_breakdown = {}

    # Multi-column layout
    if extraction.get("has_columns", False):
        penalty = 25
        ats_score -= penalty
        ats_breakdown["multi_column"] = -penalty
        issues.append({
            "severity": "critical",
            "category": "ats_structure",
            "title": "Multi-column layout detected",
            "detail": "2005-era ATS systems read left-to-right, top-to-bottom in a single pass. Columns cause content to be read in the wrong order or completely scrambled. A two-column resume becomes word soup.",
            "points_lost": penalty,
        })
        suggestions.append("Use a single-column layout. Move skills, contact info, and other sidebar content to the main column.")

    # Tables
    if extraction.get("has_tables", False):
        penalty = 20
        ats_score -= penalty
        ats_breakdown["has_tables"] = -penalty
        issues.append({
            "severity": "high",
            "category": "ats_structure",
            "title": "Tables detected",
            "detail": "ATS parsers from this era often skip table content entirely or mangle the cell order. Skills tables, experience grids, and side-by-side comparisons all fail.",
            "points_lost": penalty,
        })
        suggestions.append("Replace all tables with simple bullet lists or plain text sections. No skill matrices.")

    # Headers/Footers
    if extraction.get("has_headers_footers", False):
        penalty = 10
        ats_score -= penalty
        ats_breakdown["headers_footers"] = -penalty
        issues.append({
            "severity": "medium",
            "category": "ats_structure",
            "title": "Page headers/footers detected",
            "detail": "Many ATS parsers ignore header and footer regions. Contact info, name, or page numbers in these areas may be completely missed.",
            "points_lost": penalty,
        })
        suggestions.append("Keep your name and contact info in the main body, not in page headers or footers.")

    # Section detection
    detected_sections = _detect_sections(text_lower)
    missing_critical = []
    for section in ["contact", "experience", "education", "skills"]:
        if section not in detected_sections:
            missing_critical.append(section)

    if missing_critical:
        penalty = len(missing_critical) * 8
        ats_score -= penalty
        ats_breakdown["missing_sections"] = -penalty
        issues.append({
            "severity": "high",
            "category": "ats_structure",
            "title": f"Missing critical sections: {', '.join(missing_critical)}",
            "detail": f"ATS systems expect standard section headers to categorize your information. Without these headers, the parser cannot place content into the right buckets and may discard it.",
            "points_lost": penalty,
        })
        for s in missing_critical:
            suggestions.append(f"Add a clearly labeled '{s.title()}' section with that exact word as the heading.")

    # Section order check
    section_order_penalty = _check_section_order(text_lower, detected_sections)
    if section_order_penalty > 0:
        ats_score -= section_order_penalty
        ats_breakdown["section_order"] = -section_order_penalty
        issues.append({
            "severity": "low",
            "category": "ats_structure",
            "title": "Non-standard section order",
            "detail": "ATS systems expect: Contact → Summary → Experience → Education → Skills. Unusual ordering can confuse parsers.",
            "points_lost": section_order_penalty,
        })

    # Line length analysis (very long lines = formatting artifacts)
    long_lines = [l for l in raw_text.split('\n') if len(l) > 200]
    if len(long_lines) > 5:
        penalty = 8
        ats_score -= penalty
        ats_breakdown["long_lines"] = -penalty
        issues.append({
            "severity": "low",
            "category": "ats_structure",
            "title": "Abnormally long text lines detected",
            "detail": f"{len(long_lines)} lines exceed 200 characters, suggesting text boxes or columns are being merged into single lines by the parser.",
            "points_lost": penalty,
        })

    # File-type specific checks
    if extraction.get("file_type") == "pdf":
        page_count = extraction.get("page_count", 1)
        if page_count > 2:
            penalty = 5
            ats_score -= penalty
            ats_breakdown["too_many_pages"] = -penalty
            issues.append({
                "severity": "low",
                "category": "ats_structure",
                "title": f"Resume is {page_count} pages",
                "detail": "Many ATS systems only parse the first 1–2 pages. Content on page 3+ may be ignored entirely.",
                "points_lost": penalty,
            })

    # Date format check
    date_issues = _check_date_formats(raw_text)
    if date_issues:
        penalty = 5
        ats_score -= penalty
        ats_breakdown["date_formats"] = -penalty
        issues.append({
            "severity": "low",
            "category": "ats_structure",
            "title": "Non-standard date formats",
            "detail": f"Found dates like: {', '.join(date_issues[:3])}. Old ATS systems prefer MM/YYYY or Month YYYY format.",
            "points_lost": penalty,
        })

    # URL/contact parsing
    contact_score = _check_contact_info(raw_text)
    if contact_score["penalty"] > 0:
        ats_score -= contact_score["penalty"]
        ats_breakdown["contact_issues"] = -contact_score["penalty"]
        for issue in contact_score["issues"]:
            issues.append(issue)

    ats_score = max(0, ats_score)

    # --- 3. OVERALL SCORE ---
    overall_score = round((readability_score * 0.45) + (ats_score * 0.55))

    # --- 4. WHAT THE ATS ACTUALLY READS ---
    ats_visible_text = _simulate_ats_view(raw_text, extraction)

    # --- 5. PARSED SECTIONS ---
    parsed_sections = _parse_sections_detailed(raw_text, detected_sections)

    # --- 6. GRADE ---
    grade = _compute_grade(overall_score)

    # --- 7. POSITIVE FINDINGS ---
    positives = _find_positives(extraction, detected_sections, raw_text)

    # Sort issues by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "overall_score": overall_score,
        "readability_score": readability_score,
        "ats_score": ats_score,
        "grade": grade,
        "issues": issues,
        "suggestions": list(set(suggestions)),
        "positives": positives,
        "detected_sections": list(detected_sections.keys()),
        "parsed_sections": parsed_sections,
        "ats_visible_text": ats_visible_text,
        "text_blocks": extraction.get("text_blocks", []),
        "metadata": {
            "word_count": extraction.get("word_count", 0),
            "char_count": extraction.get("char_count", 0),
            "page_count": extraction.get("page_count", 1),
            "fonts_used": extraction.get("fonts_used", []),
            "has_images": extraction.get("has_images", False),
            "has_tables": extraction.get("has_tables", False),
            "has_columns": extraction.get("has_columns", False),
            "has_headers_footers": extraction.get("has_headers_footers", False),
            "file_type": extraction.get("file_type", "unknown"),
            "extraction_method": extraction.get("extraction_method", "unknown"),
        },
        "readability_breakdown": readability_breakdown,
        "ats_breakdown": ats_breakdown,
    }


def _detect_sections(text_lower: str) -> dict[str, int]:
    """Detect which standard resume sections are present. Returns section_name -> char_position."""
    detected = {}
    for section_name, patterns in SECTION_HEADERS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                detected[section_name] = match.start()
                break
    return detected


def _check_section_order(text_lower: str, detected: dict) -> int:
    """Penalize non-standard section ordering. Returns penalty points."""
    ideal_order = ["contact", "summary", "experience", "education", "skills"]
    present = [s for s in ideal_order if s in detected]
    if len(present) < 3:
        return 0
    positions = [detected[s] for s in present]
    if positions != sorted(positions):
        return 5
    return 0


def _check_date_formats(text: str) -> list[str]:
    """Find non-standard date formats that ATS systems struggle with."""
    bad_date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
        r'\b\d{4}-\d{2}-\d{2}\b',          # YYYY-MM-DD (ISO, not common in resumes)
        r"'\d{2}\b",                         # '22 (abbreviated year)
    ]
    found = []
    for pattern in bad_date_patterns:
        matches = re.findall(pattern, text)
        found.extend(matches[:2])
    return found[:5]


def _check_contact_info(text: str) -> dict:
    """Check contact information parsing issues."""
    issues = []
    penalty = 0

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\+?1?\s?)?(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]\d{4})\b'

    has_email = bool(re.search(email_pattern, text))
    has_phone = bool(re.search(phone_pattern, text))

    if not has_email:
        penalty += 8
        issues.append({
            "severity": "high",
            "category": "contact",
            "title": "No parseable email address found",
            "detail": "ATS systems need to extract your email to contact you. Ensure it's in plain text, not in an image or styled element.",
            "points_lost": 8,
        })

    if not has_phone:
        penalty += 5
        issues.append({
            "severity": "medium",
            "category": "contact",
            "title": "No parseable phone number found",
            "detail": "Phone number not detected in standard format. Use: (555) 555-5555 or 555-555-5555.",
            "points_lost": 5,
        })

    return {"penalty": penalty, "issues": issues}


def _simulate_ats_view(raw_text: str, extraction: dict) -> str:
    """
    Simulate what a 2005 ATS actually sees after parsing.
    Apply realistic transformations: strip special chars, normalize whitespace, etc.
    """
    text = raw_text

    # Replace special characters with ATS equivalents or garbage
    replacements = {
        '\u2022': '*',      # bullet → asterisk
        '\u2019': "'",      # smart apostrophe
        '\u2018': "'",
        '\u201c': '"',      # smart quotes
        '\u201d': '"',
        '\u2013': '-',      # en-dash
        '\u2014': '--',     # em-dash
        '\u00a0': ' ',      # non-breaking space
        '\u200b': '',       # zero-width space
        '\u2026': '...',    # ellipsis
        '\ufffd': '?',      # replacement char
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Normalize excessive whitespace (ATS collapses it)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)

    # If columns detected, add warning prefix
    if extraction.get("has_columns"):
        text = "[COLUMN PARSING WARNING: Text order may be scrambled]\n\n" + text

    if extraction.get("has_tables"):
        text = "[TABLE CONTENT MAY BE PARTIALLY SKIPPED]\n\n" + text

    return text.strip()


def _parse_sections_detailed(raw_text: str, detected_sections: dict) -> dict:
    """Extract the actual content of each detected section."""
    if not detected_sections:
        return {}

    lines = raw_text.split('\n')
    sections_content = {}

    section_line_map = {}
    for section_name in detected_sections:
        patterns = SECTION_HEADERS.get(section_name, [])
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for pattern in patterns:
                if re.search(pattern, line_lower) and len(line_lower) < 50:
                    section_line_map[i] = section_name
                    break

    # Extract content between section headers
    sorted_sections = sorted(section_line_map.items())
    for idx, (line_num, section_name) in enumerate(sorted_sections):
        if idx + 1 < len(sorted_sections):
            next_line = sorted_sections[idx + 1][0]
            content_lines = lines[line_num + 1:next_line]
        else:
            content_lines = lines[line_num + 1:line_num + 30]

        content = '\n'.join(l for l in content_lines if l.strip()).strip()
        sections_content[section_name] = content[:1000]

    return sections_content


def _find_positives(extraction: dict, detected_sections: dict, raw_text: str) -> list[str]:
    """Find things the resume does right."""
    positives = []

    if not extraction.get("has_columns"):
        positives.append("Single-column layout — ATS can parse top-to-bottom correctly")

    if not extraction.get("has_images") and extraction.get("non_text_ratio", 0) < 0.1:
        positives.append("No embedded images — all content is machine-readable text")

    if not extraction.get("has_tables"):
        positives.append("No tables detected — content won't be scrambled by the parser")

    word_count = extraction.get("word_count", 0)
    if 300 <= word_count <= 800:
        positives.append(f"Good word count ({word_count} words) — enough content for keyword matching")

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, raw_text):
        positives.append("Email address is parseable in plain text")

    if "experience" in detected_sections:
        positives.append("Work experience section detected and labeled clearly")

    if "education" in detected_sections:
        positives.append("Education section detected and labeled clearly")

    if "skills" in detected_sections:
        positives.append("Skills section detected — keyword matching will work here")

    if not extraction.get("has_headers_footers"):
        positives.append("No page headers/footers — contact info is in the main body")

    fonts = [f.lower() for f in extraction.get("fonts_used", [])]
    safe = [f for f in fonts if any(s in f for s in SAFE_FONTS)]
    if safe:
        positives.append(f"ATS-safe font(s) detected: {', '.join(safe[:2])}")

    return positives[:8]


def _compute_grade(score: int) -> dict:
    """Convert numeric score to letter grade with label."""
    if score >= 90:
        return {"letter": "A", "label": "ATS Ready", "color": "#16a34a"}
    elif score >= 75:
        return {"letter": "B", "label": "Mostly Compatible", "color": "#65a30d"}
    elif score >= 60:
        return {"letter": "C", "label": "Needs Work", "color": "#d97706"}
    elif score >= 45:
        return {"letter": "D", "label": "At Risk", "color": "#ea580c"}
    else:
        return {"letter": "F", "label": "ATS Will Reject", "color": "#dc2626"}
