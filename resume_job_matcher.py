from __future__ import annotations

import argparse
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence
from zipfile import ZipFile


MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

DISPLAY = {
    "api": "API", "apis": "APIs", "aws": "AWS", "json": "JSON", "yaml": "YAML",
    "grpc": "gRPC", "sql": "SQL", "nosql": "NoSQL", "c++": "C++", "c#": "C#",
    ".net": ".NET", "typescript": "TypeScript", "javascript": "JavaScript",
    "node.js": "Node.js", "postgresql": "PostgreSQL", "mysql": "MySQL",
    "db2": "DB2", "ci/cd": "CI/CD", "ai/ml": "AI/ML", "ui/ux": "UI/UX",
}

SKILL_PATTERNS = [
    ("Spring Boot", (r"\bspring\s*boot\b",)),
    (".NET", (r"\b\.net\b", r"\bdot\s*net\b")),
    ("Node.js", (r"\bnode\.?\s*js\b", r"\bnodejs\b")),
    ("Express", (r"\bexpress(?:\.js)?\b",)),
    ("React", (r"\breact(?:\.js)?\b",)),
    ("Angular", (r"\bangular(?:js)?\b",)),
    ("TypeScript", (r"\btypescript\b",)),
    ("JavaScript", (r"\bjavascript\b",)),
    ("Java", (r"\bcore\s+java\b", r"\bjava\b(?!script)")),
    ("Python", (r"\bpython\b",)),
    ("C++", (r"\bc\+\+\b",)),
    ("C#", (r"\bc#\b", r"\bc\s*sharp\b")),
    ("Rust", (r"\brust\b",)),
    ("Go", (r"\bgolang\b", r"\bgo\b(?=\s*[,/)])", r"\bgo\b(?=\s+or\b)")),
    ("Fortran", (r"\bfortran\b",)),
    ("C", (r"(?<![a-z0-9])c(?![a-z0-9+#])",)),
    ("Microsoft SQL Server", (r"\b(?:microsoft\s+sql\s+server|sql\s+server)\b",)),
    ("PostgreSQL", (r"\bpostgres(?:ql)?\b",)),
    ("MySQL", (r"\bmysql\b",)),
    ("DB2", (r"\b(?:db2|udbdb2)\b",)),
    ("MongoDB", (r"\bmongodb\b",)),
    ("NoSQL", (r"\bno\s*sql\b", r"\bnosql\b")),
    ("SQL", (r"\bsql\b",)),
    ("REST API", (r"\brest(?:ful)?\s*api(?:s)?\b", r"\bapi design\b")),
    ("gRPC", (r"\bgrpc\b",)),
    ("Microservices", (r"\bmicroservices?\b",)),
    ("Kafka", (r"\bkafka\b",)),
    ("Docker", (r"\bdocker\b",)),
    ("Kubernetes", (r"\bkubernetes\b",)),
    ("Jenkins", (r"\bjenkins\b",)),
    ("TeamCity", (r"\bteam\s*city\b", r"\bteamcity\b")),
    ("Ansible", (r"\bansible\b",)),
    ("Terraform", (r"\bterraform\b",)),
    ("Chef", (r"\bchef\b",)),
    ("AWS", (r"\baws\b", r"\bamazon\s+web\s+services\b")),
    ("Azure", (r"\bazure\b",)),
    ("Linux", (r"\blinux\b",)),
    ("Unix", (r"\bunix\b", r"\bunix-like\b")),
    ("Windows", (r"\bwindows\b",)),
    ("Git", (r"\bgit\b", r"\bversion\s+control\b")),
    ("SVN", (r"\bsvn\b",)),
    ("ClearCase", (r"\bclearcase\b",)),
    ("Agile", (r"\bagile\b",)),
    ("Scrum", (r"\bscrum\b",)),
    ("Kanban", (r"\bkanban\b",)),
    ("Unit Testing", (r"\bunit\s+testing\b", r"\bunit\s+tests?\b")),
    ("Software Testing", (r"\bsoftware\s+testing\b", r"\btest\s+automation\b")),
    ("DevOps", (r"\bdevops\b",)),
    ("CI/CD", (r"\bci\s*/?\s*cd\b", r"\bcontinuous\s+integration\b")),
    ("Cloud Native", (r"\bcloud-native\b", r"\bcloud\s+native\b")),
    ("Cloud", (r"\bcloud\b",)),
    ("Full Stack Development", (r"\bfull[\s-]?stack\b",)),
    ("UI/UX", (r"\bui\s*/\s*ux\b", r"\buser\s+interface\s+design\b")),
    ("UI Development", (r"\bui\s+development\b",)),
    ("Back-end Development", (r"\bback[\s-]?end\s+development\b",)),
    ("Web Services", (r"\bweb\s+service(?:s)?\b",)),
    ("High Performance Computing", (r"\bhigh[-\s]+performance\s+comput(?:ing|ers?)\b", r"\bhpc\b")),
    ("Parallel Programming", (r"\bparallel\s+programming\b",)),
    ("MPI", (r"\bmpi\b",)),
    ("OpenMP", (r"\bopenmp\b",)),
    ("Data Pipelines", (r"\bdata\s+pipelines?\b",)),
    ("Telemetry", (r"\btelemetry\b",)),
    ("Time Series", (r"\btime[-\s]?series\b",)),
    ("JSON", (r"\bjson\b",)),
    ("YAML", (r"\byaml\b",)),
    ("Protobuf", (r"\bprotobuf\b",)),
    ("Bash", (r"\bbash\b",)),
    ("Shell Scripting", (r"\bshell\s+scripting\b", r"\bunix\s+shell\s+scripting\b")),
    ("HTML", (r"\bhtml\b",)),
    ("CSS", (r"\bcss\b",)),
    ("ELK Stack", (r"\belk\s+stack\b",)),
    ("Elasticsearch", (r"\belastic\s*search\b", r"\belasticsearch\b")),
    ("Kibana", (r"\bkibana\b",)),
    ("Logstash", (r"\blogstash\b",)),
    ("Prometheus", (r"\bprometheus\b",)),
    ("Grafana", (r"\bgrafana\b",)),
    ("Embedded Systems", (r"\bembedded\s+system(?:s)?\b",)),
    ("RTOS", (r"\brtos\b", r"\breal[-\s]+time\s+operating\s+systems?\b")),
    ("PyTorch", (r"\bpytorch\b",)),
    ("Machine Learning", (r"\bmachine\s+learning\b",)),
    ("AI/ML", (r"\bai\s*/\s*ml\b", r"\bai\s+ml\b")),
    ("Computer Vision", (r"\bcomputer\s+vision\b",)),
    ("Signal Processing", (r"\bsignal\s+processing\b",)),
    ("Robotics", (r"\brobotics\b",)),
    ("FPGA", (r"\bfpga\b",)),
    ("Numerical Methods", (r"\bnumerical\s+methods?\b", r"\bnumerical\s+algorithms?\b")),
    ("Linear Algebra", (r"\blinear\s+algebra\b",)),
    ("SaaS", (r"\bsaas\b",)),
]

SKILL_REGEX = [(name, tuple(re.compile(p, re.I) for p in patterns)) for name, patterns in SKILL_PATTERNS]
SKILL_LOOKUP = {re.sub(r"[^a-z0-9+#./]+", " ", name.lower()).strip(): name for name, _ in SKILL_PATTERNS}

ROLE_HINTS = ("software engineer", "backend developer", "developer", "programmer", "architect")
RESUME_HEADINGS = {"resume", "profile", "summary", "experience", "skills", "education", "projects"}
REQ_HEADERS = ("required qualifications", "minimum qualifications", "must have", "required skills", "basic qualifications", "requirements", "qualifications", "what you need to have", "what you need to succeed", "why we value you")
OPT_HEADERS = ("desired qualifications", "preferred qualifications", "desired skills", "good to have", "nice to haves", "what we'd like you to have", "what we d like you to have", "desired multipliers")
SUMMARY_HEADERS = ("position overview", "job description", "overview", "the opportunity", "what you'll do", "what you ll do", "how you'll fulfill your mission", "how you ll fulfill your mission", "responsibilities", "role responsibilities")
STOP_HEADERS = set(REQ_HEADERS + OPT_HEADERS + SUMMARY_HEADERS + ("salary", "global comp", "additional information", "other important information", "closing statement", "benefits", "compensation and benefits"))
SHORT_SKILL_STOPWORDS = {"software engineer", "job description", "salary range", "desired skills", "required skills", "good to have", "ability to work remotely"}
DATE_RANGE = re.compile(r"(?P<start>(?:[A-Za-z]{3,9}\s+\d{4}|\d{1,2}/\d{4}|\d{4}))\s*(?:-|to|–|—)\s*(?P<end>(?:present|current|now|today|till\s+date|[A-Za-z]{3,9}\s+\d{4}|\d{1,2}/\d{4}|\d{4}))", re.I)
EXPERIENCE = re.compile(r"(?P<first>\d+(?:\.\d+)?)\s*(?:[-–]\s*(?P<second>\d+(?:\.\d+)?))?\s*\+?\s*years?(?:\s+of)?(?:\s+[a-zA-Z/-]+){0,4}\s+experience", re.I)


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    replacements = {"\r\n": "\n", "\r": "\n", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\xa0": " "}
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = text.replace("AlML", "AI ML").replace("modernizingrewriting", "modernizing rewriting")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_search(text: str) -> str:
    return collapse_spaces(re.sub(r"[^a-z0-9+#./]+", " ", normalize_text(text).lower()))


def normalize_skill_key(text: str) -> str:
    return collapse_spaces(re.sub(r"[^a-z0-9+#./]+", " ", normalize_text(text).lower()))


def stable_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        key = normalize_skill_key(value)
        if not value or key in seen:
            continue
        seen.add(key)
        items.append(value)
    return items


def prettify(text: str) -> str:
    cleaned = collapse_spaces(text.strip(" .,:;\"'"))
    key = normalize_skill_key(cleaned)
    if key in SKILL_LOOKUP:
        return SKILL_LOOKUP[key]
    words: list[str] = []
    for word in cleaned.split():
        parts = word.split("/")
        rendered = []
        for part in parts:
            lower = part.lower()
            rendered.append(DISPLAY.get(lower, part if part.isupper() and len(part) <= 6 else part.capitalize()))
        words.append("/".join(rendered))
    return " ".join(words)


def split_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in normalize_text(text).splitlines():
        line = collapse_spaces(re.sub(r"^[\-\u2022*]+\s*", "", raw))
        if line:
            lines.append(line)
    return lines


def read_docx(path: Path) -> str:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    return "\n".join(node.text for node in root.iter() if node.text)


def read_docx_bytes(data: bytes) -> str:
    with ZipFile(io.BytesIO(data)) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    return "\n".join(node.text for node in root.iter() if node.text)


def read_pdf(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        pass
    try:
        import fitz  # type: ignore

        document = fitz.open(path)
        try:
            return "\n".join(page.get_text("text") for page in document)
        finally:
            document.close()
    except Exception:
        pass
    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ValueError(f"Unable to read PDF: {path}") from exc


def read_pdf_bytes(data: bytes, source_name: str = "uploaded.pdf") -> str:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        pass
    try:
        import fitz  # type: ignore

        document = fitz.open(stream=data, filetype="pdf")
        try:
            return "\n".join(page.get_text("text") for page in document)
        finally:
            document.close()
    except Exception:
        pass
    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ValueError(f"Unable to read PDF: {source_name}") from exc


def load_document(path: str | Path) -> str:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix in {".txt", ".md"}:
        return normalize_text(source.read_text(encoding="utf-8"))
    if suffix == ".docx":
        return normalize_text(read_docx(source))
    if suffix == ".pdf":
        return normalize_text(read_pdf(source))
    raise ValueError(f"Unsupported file type: {suffix}")


def load_document_bytes(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return normalize_text(data.decode("utf-8", errors="ignore"))
    if suffix == ".docx":
        return normalize_text(read_docx_bytes(data))
    if suffix == ".pdf":
        return normalize_text(read_pdf_bytes(data, source_name=filename))
    raise ValueError(f"Unsupported file type: {suffix}")


def clean_numeric(value: float | None) -> float | int | None:
    if value is None:
        return None
    rounded = round(value, 2)
    if abs(rounded - round(rounded)) < 1e-9:
        return int(round(rounded))
    return round(rounded, 1)


def extract_name(text: str) -> str | None:
    for line in split_lines(text)[:12]:
        lowered = line.lower()
        if lowered in RESUME_HEADINGS:
            continue
        if any(token in lowered for token in ("@", "linkedin", "github", "email", "phone", "http", "www.")):
            continue
        if any(char.isdigit() for char in line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            titled = sum(1 for word in words if word[:1].isupper() or word.isupper())
            if titled >= len(words) - 1:
                return " ".join(word.title() if word.isupper() else word for word in words)
    return None


def extract_salary_candidate(text: str) -> str | None:
    range_pattern = re.compile(r"(?:[$₹]|USD|INR|Rs\.?)?\s*\d[\d,]*(?:\.\d+)?\s*(?:LPA|lakhs?|cr|crore|/hour|/hr|/year|per year|per annum|annually|USD)?\s*(?:-|to|--)\s*(?:[$₹]|USD|INR|Rs\.?)?\s*\d[\d,]*(?:\.\d+)?\s*(?:LPA|lakhs?|cr|crore|/hour|/hr|/year|per year|per annum|annually|USD)?", re.I)
    single_pattern = re.compile(r"(?:[$₹]|USD|INR|Rs\.?)\s*\d[\d,]*(?:\.\d+)?(?:\s*(?:/hour|/hr|/year|per year|per annum|annually|USD))?", re.I)
    lpa_pattern = re.compile(r"\b\d+(?:\.\d+)?\s*LPA\b", re.I)
    for pattern in (range_pattern, lpa_pattern, single_pattern):
        match = pattern.search(text)
        if match:
            return collapse_spaces(match.group(0).strip(" .,:;"))
    return None


def extract_salary(text: str) -> str | None:
    lines = split_lines(text)
    labels = ("salary", "ctc", "compensation", "pay range", "base pay range", "base compensation range", "global comp")
    for index, line in enumerate(lines):
        if any(label in line.lower() for label in labels):
            candidate = extract_salary_candidate(line)
            if candidate:
                return candidate
            if index + 1 < len(lines):
                candidate = extract_salary_candidate(lines[index + 1])
                if candidate:
                    return candidate
    return extract_salary_candidate(text)


def extract_explicit_experience(text: str) -> float | None:
    values: list[float] = []
    if re.search(r"\b(fresher|entry[\s-]?level)\b", text, re.I):
        values.append(0.0)
    for match in EXPERIENCE.finditer(normalize_text(text)):
        values.append(float(match.group("first")))
    return max(values) if values else None


def parse_date_token(token: str, is_end: bool) -> tuple[int, int] | None:
    current = date.today()
    cleaned = collapse_spaces(token.lower().replace(".", ""))
    if cleaned in {"present", "current", "now", "today", "till date"}:
        return current.year, current.month
    month_year = re.fullmatch(r"([a-z]{3,9})\s+(\d{4})", cleaned)
    if month_year and month_year.group(1) in MONTHS:
        return int(month_year.group(2)), MONTHS[month_year.group(1)]
    numeric = re.fullmatch(r"(\d{1,2})/(\d{4})", cleaned)
    if numeric:
        month = int(numeric.group(1))
        if 1 <= month <= 12:
            return int(numeric.group(2)), month
    year_only = re.fullmatch(r"(\d{4})", cleaned)
    if year_only:
        return int(year_only.group(1)), 12 if is_end else 1
    return None


def extract_date_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for match in DATE_RANGE.finditer(normalize_text(text)):
        start = parse_date_token(match.group("start"), is_end=False)
        end = parse_date_token(match.group("end"), is_end=True)
        if not start or not end:
            continue
        start_index = start[0] * 12 + start[1]
        end_index = end[0] * 12 + end[1]
        if end_index >= start_index:
            ranges.append((start_index, end_index))
    return ranges


def merge_ranges(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def extract_experience_from_dates(text: str) -> float | None:
    ranges = merge_ranges(extract_date_ranges(text))
    if not ranges:
        return None
    total_months = sum(end - start + 1 for start, end in ranges)
    return round(total_months / 12.0, 1)


def extract_experience_years(text: str, *, allow_date_fallback: bool) -> float | int | None:
    explicit = extract_explicit_experience(text)
    if explicit is not None:
        return clean_numeric(explicit)
    if allow_date_fallback:
        return clean_numeric(extract_experience_from_dates(text))
    return None


def normalize_header(line: str) -> str:
    return collapse_spaces(re.sub(r"[^a-z0-9]+", " ", line.lower()))


def extract_section(text: str, headers: Sequence[str]) -> str:
    blocks: list[str] = []
    current: list[str] = []
    active = False
    for line in split_lines(text):
        header = normalize_header(line)
        if len(header.split()) <= 8 and any(stop in header for stop in STOP_HEADERS):
            if active and current:
                blocks.append("\n".join(current))
                current = []
            active = any(target in header for target in headers)
            continue
        if len(header.split()) <= 8 and any(target in header for target in headers):
            if active and current:
                blocks.append("\n".join(current))
                current = []
            active = True
            continue
        if active:
            current.append(line)
    if active and current:
        blocks.append("\n".join(current))
    return "\n".join(blocks).strip()


def extract_dynamic_skills(text: str) -> list[str]:
    items: list[str] = []
    for line in split_lines(text):
        parts = [line] if "," not in line else [part.strip() for part in line.split(",")]
        for part in parts:
            cleaned = collapse_spaces(part.strip(" .:;\"'"))
            lowered = cleaned.lower()
            if not cleaned or len(cleaned) < 2 or len(cleaned) > 50:
                continue
            word_count = len(cleaned.split())
            if lowered in SHORT_SKILL_STOPWORDS or word_count > 4:
                continue
            if any(char.isdigit() for char in cleaned):
                continue
            if any(symbol in cleaned for symbol in ("(", ")", ".")):
                continue
            if re.search(r"\b(experience|clearance|degree|benefits|salary|compensation|travel|citizenship|location|onsite|remote)\b", lowered):
                continue
            if re.search(r"\b(should|used|built|developed|worked|including|proven|familiarity|exposure|valuable|required|support|responsible|ability)\b", lowered):
                continue
            if any(lowered.startswith(prefix) for prefix in ("ability to ", "demonstrated experience ", "bachelor", "master", "phd", "experience ", "exposure ", "familiarity ")):
                continue
            if lowered.startswith(("and ", "or ", "with ", "for ", "to ")):
                continue
            if re.search(r"\b(and|or|with|for|to|of)\b", lowered) and word_count > 2:
                continue
            if any(char.isalpha() for char in cleaned):
                items.append(prettify(cleaned))
    return stable_unique(items)


def extract_skills(text: str, *, include_dynamic: bool = True) -> list[str]:
    normalized = normalize_text(text)
    skills: list[str] = []
    for name, patterns in SKILL_REGEX:
        if any(pattern.search(normalized) for pattern in patterns):
            skills.append(name)
    if include_dynamic:
        skills.extend(extract_dynamic_skills(text))
    return stable_unique(skills)


def extract_role(text: str, fallback: str) -> str:
    for line in split_lines(text)[:30]:
        lowered = line.lower()
        if len(line) <= 90 and any(hint in lowered for hint in ROLE_HINTS):
            return line.strip(" :")
    match = re.search(r"(?:position|role)\s+(?:is|for|as)\s+(?:an?\s+)?([A-Za-z0-9/+\- ]{4,80}?(?:Engineer|Developer|Programmer|Architect))", normalize_text(text), re.I)
    return prettify(match.group(1)) if match else fallback


def extract_about_role(text: str) -> str:
    block = extract_section(text, SUMMARY_HEADERS) or normalize_text(text)
    sentences = [collapse_spaces(s) for s in re.split(r"(?<=[.!?])\s+", block) if s.strip()]
    summary = " ".join(sentences[:2])
    if len(summary) > 320:
        summary = " ".join(summary.split()[:45]).rstrip(" ,")
    return summary


def extract_jd_skills(text: str) -> tuple[list[str], list[str], list[str]]:
    required_section = extract_section(text, REQ_HEADERS)
    optional_section = extract_section(text, OPT_HEADERS)
    required = extract_skills(required_section) if required_section else []
    optional = extract_skills(optional_section) if optional_section else []
    if not required:
        required = extract_skills(text, include_dynamic=False)
    all_skills = stable_unique(required + optional)
    if not required:
        required = [skill for skill in all_skills if normalize_skill_key(skill) not in {normalize_skill_key(s) for s in optional}]
    return required, optional, all_skills


def parse_resume(text: str) -> dict[str, object]:
    normalized = normalize_text(text)
    return {
        "name": extract_name(normalized),
        "salary": extract_salary(normalized),
        "yearOfExperience": extract_experience_years(normalized, allow_date_fallback=True),
        "resumeSkills": extract_skills(normalized, include_dynamic=False),
        "_normalized": normalized,
    }


def skill_present(skill: str, resume_text: str, resume_skill_keys: set[str]) -> bool:
    skill_key = normalize_skill_key(skill)
    if skill_key in resume_skill_keys:
        return True
    known = SKILL_LOOKUP.get(skill_key)
    if known:
        patterns = dict(SKILL_REGEX)[known]
        return any(pattern.search(resume_text) for pattern in patterns)
    return skill_key in normalize_for_search(resume_text)


def build_result(resume_text: str, jobs: Sequence[tuple[str, str, str]]) -> dict[str, object]:
    resume = parse_resume(resume_text)
    resume_text_norm = str(resume["_normalized"])
    resume_skill_keys = {normalize_skill_key(skill) for skill in resume["resumeSkills"]}  # type: ignore[arg-type]
    matching_jobs: list[dict[str, object]] = []
    for job_id, file_name, job_text in jobs:
        required, optional, all_skills = extract_jd_skills(job_text)
        skills_analysis = [{"skill": skill, "presentInResume": skill_present(skill, resume_text_norm, resume_skill_keys)} for skill in all_skills]
        matched = sum(1 for item in skills_analysis if item["presentInResume"])
        score = 0.0 if not all_skills else round((matched / len(all_skills)) * 100, 2)
        job_data: dict[str, object] = {
            "jobId": job_id,
            "role": extract_role(job_text, prettify(Path(file_name).stem.replace("_", " ").replace("-", " "))),
            "aboutRole": extract_about_role(job_text),
            "requiredSkills": required,
            "optionalSkills": optional,
            "skillsAnalysis": skills_analysis,
            "matchingScore": clean_numeric(score),
        }
        salary = extract_salary(job_text)
        years = extract_experience_years(job_text, allow_date_fallback=False)
        if salary is not None:
            job_data["salary"] = salary
        if years is not None:
            job_data["yearOfExperience"] = years
        matching_jobs.append(job_data)
    matching_jobs.sort(key=lambda item: float(item["matchingScore"]), reverse=True)
    return {
        "name": resume["name"],
        "salary": resume["salary"],
        "yearOfExperience": resume["yearOfExperience"],
        "resumeSkills": resume["resumeSkills"],
        "matchingJobs": matching_jobs,
    }


def load_jobs(paths: Sequence[Path]) -> list[tuple[str, str, str]]:
    return [(f"JD{index:03d}", path.name, load_document(path)) for index, path in enumerate(paths, start=1)]


def demo_paths() -> tuple[Path, list[Path]]:
    base = Path(__file__).resolve().parent
    return base / "sample_resume.txt", [base / "sample_jd_astra.txt", base / "sample_jd_capgemini.txt"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rule-based resume parser and JD matcher.")
    parser.add_argument("--resume", help="Resume file path (.txt, .pdf, .docx)")
    parser.add_argument("--jd", action="append", default=[], help="Job description file path")
    parser.add_argument("--jd-dir", help="Directory containing JD files")
    parser.add_argument("--output", help="Write output JSON to this file")
    parser.add_argument("--demo", action="store_true", help="Run the bundled sample files")
    args = parser.parse_args(argv)

    if args.demo:
        resume_path, jd_paths = demo_paths()
        resume_text = load_document(resume_path)
        jobs = load_jobs(jd_paths)
    else:
        if not args.resume:
            parser.error("--resume is required unless --demo is used")
        paths = [Path(path) for path in args.jd]
        if args.jd_dir:
            paths.extend(sorted(path for path in Path(args.jd_dir).iterdir() if path.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}))
        if not paths:
            parser.error("Provide at least one --jd or --jd-dir")
        resume_text = load_document(args.resume)
        jobs = load_jobs(paths)

    payload = json.dumps(build_result(resume_text, jobs), indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0
