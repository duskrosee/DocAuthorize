"""Rule-based document analysis for Polish/English contracts and agreements."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import pdfplumber

from services.pdf_reader import ProcessedPDF, TextSegment, TextSource

NOT_FOUND = "Not found"

NIP_PATTERN = re.compile(r"\b(?:\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}|\d{10})\b")

EMAIL_PATTERN = re.compile(
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,4}[-.\s]?)?"
    r"(?:\(?\d{1,5}\)?[-.\s]?)?"
    r"\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,9}"
)

COMPANY_PHONE_LABEL_PATTERN = re.compile(
    r"(?i)"
    r"(?:"
    r"telefon\s+firmy|telefon\s+do\s+firmy|tel\.\s*firmy|tel\.\s*|telefon"
    r"|company\s+phone|company\s+tel|office\s+phone"
    r")"
    r"\s*[:\-]?\s*"
    r"(?P<phone>" + PHONE_PATTERN.pattern + r")"
)

CONTACT_PHONE_LABEL_PATTERN = re.compile(
    r"(?i)"
    r"(?:"
    r"telefon\s+kontaktowy|telefon\s+osoby|tel\.\s+kontaktowy|tel\.\s+osoby"
    r"|nr\s+telefonu|numer\s+telefonu|contact\s+phone|mobile|phone"
    r")"
    r"\s*[:\-]?\s*"
    r"(?P<phone>" + PHONE_PATTERN.pattern + r")"
)

PRICE_PATTERN = re.compile(
    r"(?i)"
    r"(?:"
    r"cena|kwota|wartość|wynagrodzenie|wynagrodzenie\s+miesięczne|stawka|kwota\s+wynagrodzenia"
    r"|price|total\s+price|amount|fee|value"
    r")"
    r".{0,80}?"
    r"(?P<price>\d[\d\s,.]*)"
    r"\s*"
    r"(?P<currency>PLN|zł|złotych|EUR|USD|GBP|\$|€|£)"
)

DATE_REGEX = (
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})\b"
)

CONTRACT_DATE_PATTERNS = (
    re.compile(
        r"(?i)"
        r"(?:zawarte|zawarta|zawarty|zawarto|podpisane|podpisana|podpisano|signed|dated)"
        r"(?:\s+\w+){0,4}"
        r"\s+(?:w\s+dniu\s+|on\s+)?"
        r"(?P<date>" + DATE_REGEX + r")"
    ),
    re.compile(
        r"(?i)"
        r"(?:data\s+(?:zawarcia|podpisania)|data\s+umowy|contract\s+date|date\s+of\s+contract|date)"
        r"\s*[:\-]?\s*"
        r"(?P<date>" + DATE_REGEX + r")"
    ),
    re.compile(r"(?i)contract\s+date\s*[:\-]?\s*(?P<date>" + DATE_REGEX + r")"),
)

VALIDITY_PERIOD_PATTERNS = (
    re.compile(
        r"(?i)"
        r"\bod\s+(?P<start>" + DATE_REGEX + r")\s+do\s+(?P<end>" + DATE_REGEX + r")"
    ),
    re.compile(
        r"(?i)"
        r"\bfrom\s+(?P<start>" + DATE_REGEX + r")\s+to\s+(?P<end>" + DATE_REGEX + r")"
    ),
    re.compile(
        r"(?i)"
        r"(?:obowiązuje|obowiązywania|okres\s+obowiązywania|validity\s+period|valid\s+until|validity)"
        r".{0,50}?"
        r"(?P<end>" + DATE_REGEX + r")"
    ),
)

COMPANY_LABEL_PATTERN = re.compile(
    r"(?i)"
    r"(?:"
    r"firma|pracodawca|podmiot|nazwa\s+firmy|nazwa\s+pracodawcy|strona"
    r"|company|employer|client|contractor|party"
    r")"
    r"\s*[:\-]\s*"
    r"(?P<company>[^\n]{3,120})"
)

COMPANY_LEGAL_FORM_PATTERN = re.compile(
    r"(?i)"
    r"([A-ZŁŚŻŹĆŃÓ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 .,&'\"-]{2,100}"
    r"\s+"
    r"(?:"
    r"Sp\.?\s*z\.?\s*o\.?\s*o\.?|S\.?\s*A\.?|S\.?\s*C\.?|S\.?\s*J\.?|S\.?\s*K\.?\s*A\.?"
    r"|Ltd\.?|Inc\.?|LLC|Corp\.?"
    r"))"
)

PERSON_NAME_PATTERN = (
    r"([A-ZŁŚŻŹĆŃÓ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż'-]+"
    r"(?:\s+[A-ZŁŚŻŹĆŃÓ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż'-]+){1,2})"
)

CONTACT_PERSON_PATTERNS = (
    re.compile(
        r"(?i)"
        r"(?:osoba\s+do\s+kontaktu|osoba\s+kontaktowa|kontakt|koordynator|opiekun|contact\s+person|contact)"
        r"\s*[:\-]?\s*" + PERSON_NAME_PATTERN
    ),
    re.compile(
        r"(?i)"
        r"(?:imię\s+i\s+nazwisko|full\s+name|name)"
        r"\s*[:\-]?\s*" + PERSON_NAME_PATTERN
    ),
)

MANAGER_PATTERNS = (
    re.compile(
        r"(?i)"
        r"(?:"
        r"kierownik(?:\s+(?:praktyk|zakładu|działu|jednostki))?|kierownik\s+projektu|opiekun\s+praktyk|opiekun"
        r"|prezes(?:\s+zarządu)?|właściciel|manager|przełożony|project\s+manager|head\s+of\s+department"
        r")"
        r"\s*[:\-,]?\s*" + PERSON_NAME_PATTERN
    ),
    re.compile(
        r"(?i)"
        r"(?:reprezentowan[ay]\s+przez|kierowan[ay]\s+przez|represented\s+by)"
        r"\s*" + PERSON_NAME_PATTERN
    ),
)


def analyze_document(
    document: ProcessedPDF | str,
) -> dict[str, dict[str, object]]:
    segments = _segments_from_document(document)

    return {
        "NIP": _find_value(
            segments,
            NIP_PATTERN,
            lambda match: re.sub(r"[-\s]", "", match.group()),
        ),
        "Company": _find_company(segments),
        "Company phone": _find_company_phone(segments),
        "Contact person": _find_contact_person(segments),
        "Contact phone": _find_contact_phone(segments),
        "Email": _find_value(
            segments,
            EMAIL_PATTERN,
            lambda match: match.group(),
        ),
        "Contract date": _find_contract_date(segments),
        "Validity period": _find_validity_period(segments),
        "Price": _find_value(
            segments,
            PRICE_PATTERN,
            lambda match: (
                f"{match.group('price').strip()} {match.group('currency')}"
            ),
        ),
        "Manager": _find_manager(segments),
        "Status": _find_status(segments),
    }


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _segments_from_document(
    document: ProcessedPDF | str,
) -> list[TextSegment]:
    if isinstance(document, ProcessedPDF):
        return sorted(
            document.segments,
            key=lambda segment: (
                segment.source is not TextSource.PRINTED_TEXT,
                segment.requires_verification,
                segment.page_number,
            ),
        )

    return [
        TextSegment(
            page_number=1,
            text=document,
            source=TextSource.PRINTED_TEXT,
            requires_verification=False,
        )
    ]


def _find_value(
    segments: list[TextSegment],
    pattern: re.Pattern[str],
    transform: Callable[[re.Match[str]], str],
) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        match = pattern.search(text)
        if not match:
            continue

        value = transform(match).strip()
        if not value:
            continue

        return _field_from_segment(segment, value)

    return _not_found()


def _find_company(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        match = COMPANY_LABEL_PATTERN.search(text)
        if match:
            company = match.group("company").strip().rstrip(".,;:")
            if len(company) >= 3:
                return _field_from_segment(segment, company)

    for segment in segments:
        text = normalize_text(segment.text)
        match = COMPANY_LEGAL_FORM_PATTERN.search(text)
        if match:
            return _field_from_segment(segment, match.group(1).strip())

    return _not_found()


def _find_company_phone(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        match = COMPANY_PHONE_LABEL_PATTERN.search(text)
        if match:
            phone = _clean_phone(match.group("phone"))
            if not _looks_like_identifier(phone):
                return _field_from_segment(segment, phone)

    return _not_found()


def _find_contact_person(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        for pattern in CONTACT_PERSON_PATTERNS:
            match = pattern.search(text)
            if match:
                return _field_from_segment(segment, match.group(1).strip())

    return _not_found()


def _find_contact_phone(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        match = CONTACT_PHONE_LABEL_PATTERN.search(text)
        if match:
            phone = _clean_phone(match.group("phone"))
            if not _looks_like_identifier(phone):
                return _field_from_segment(segment, phone)

    for segment in segments:
        text = normalize_text(segment.text)
        contact_match = re.search(
            r"(?i)(?:osoba\s+kontaktowa|osoba\s+do\s+kontaktu|kontakt|contact\s+person|contact)",
            text,
        )
        if not contact_match:
            continue

        nearby_text = text[
            contact_match.start() : contact_match.start() + 300
        ]
        phone_match = PHONE_PATTERN.search(nearby_text)
        if phone_match:
            phone = _clean_phone(phone_match.group())
            if not _looks_like_identifier(phone):
                return _field_from_segment(segment, phone)

    return _not_found()


def _find_contract_date(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        for pattern in CONTRACT_DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                return _field_from_segment(segment, match.group("date"))

    return _not_found()


def _find_validity_period(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        for pattern in VALIDITY_PERIOD_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groupdict()
                if "start" in groups and "end" in groups and groups["start"]:
                    value = f"{groups['start']} — {groups['end']}"
                else:
                    value = groups["end"]
                return _field_from_segment(segment, value)

    return _not_found()


def _find_manager(segments: list[TextSegment]) -> dict[str, object]:
    for segment in segments:
        text = normalize_text(segment.text)
        for pattern in MANAGER_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            name = match.group(1).strip()
            if _looks_like_person_name(name):
                return _field_from_segment(segment, name)

    return _not_found()


def _find_status(segments: list[TextSegment]) -> dict[str, object]:
    """Determines whether the document is signed or awaiting signature."""
    signed_segment = None

    for segment in segments:
        text = normalize_text(segment.text)
        
        if re.search(r"(?i)(do\s+podpisu|draft|szablon)", text):
            return _field_from_segment(segment, "Pending Signature")
        
        if not signed_segment and re.search(r"(?i)(podpis|signed|podpisano)", text):
            signed_segment = segment
            
    if signed_segment:
        return _field_from_segment(signed_segment, "Signed")
        
    if segments:
        return _field_from_segment(segments[0], "Pending Signature")
        
    return _not_found()


def _clean_phone(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _looks_like_identifier(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10 and not phone.startswith("+"):
        return True
    return False


def _looks_like_person_name(name: str) -> bool:
    words = name.split()
    if len(words) < 2 or len(words) > 3:
        return False

    return all(
        re.match(
            r"^[A-ZŁŚŻŹĆŃÓĄĘ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż'-]+$",
            word,
        )
        for word in words
    )


def _field_from_segment(
    segment: TextSegment,
    value: str,
) -> dict[str, object]:
    return {
        "value": value,
        "source": segment.source.value,
        "page": segment.page_number,
        "requires_verification": segment.requires_verification,
        "confidence": segment.confidence,
    }


def _not_found() -> dict[str, object]:
    return {
        "value": NOT_FOUND,
        "source": "—",
        "page": None,
        "requires_verification": False,
        "confidence": None,
    }


def parse_contract_data(pdf_path: str) -> dict:
    """
    Wrapper around `analyze_document`, which reads a PDF and returns a flat dictionary needed for exporter.py and the interface.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"[Analyzer] Failed to read PDF {pdf_path}: {e}")
        return {}

    analysis = analyze_document(text)

    def get_val(key):
        val = analysis.get(key, {}).get("value", "N/A")
        return "N/A" if val == NOT_FOUND else str(val)

    return {
        "file_name": Path(pdf_path).name,
        "file_path": str(pdf_path),
        "nip": get_val("NIP"),
        "price": get_val("Price"),
        "contract_date": get_val("Contract date"),
        "manager": get_val("Manager"),
        "status": get_val("Status") or "Pending Signature",
    }



#.