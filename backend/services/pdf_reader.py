from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, Sequence

import fitz


class OCRPolicy(str, Enum):

    FALLBACK = "fallback"
    ALL_PAGES = "all_pages"


class OCRHint(str, Enum):

    TEXT = "text"
    HANDWRITING = "handwriting"
    STAMP = "stamp"


class TextSource(str, Enum):
    PRINTED_TEXT = "Printed text"
    OCR = "OCR"
    HANDWRITING_OCR = "Handwriting / OCR"
    STAMP_OCR = "Stamp / OCR"


class OCRUnavailableError(RuntimeError):
    """Raised when the optional OCR dependencies are not installed."""


@dataclass(frozen=True)
class OCRPageResult:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TextSegment:
    page_number: int
    text: str
    source: TextSource
    requires_verification: bool
    confidence: float | None = None


@dataclass
class ProcessedPDF:
    """All extracted text together with the source of every text segment."""

    segments: list[TextSegment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ocr_attempted: bool = False
    ocr_available: bool | None = None

    @property
    def text(self) -> str:
        return "\n\n".join(segment.text for segment in self.segments if segment.text)

    @property
    def page_count(self) -> int:
        return len({segment.page_number for segment in self.segments})

    @property
    def uses_ocr(self) -> bool:
        return any(segment.requires_verification for segment in self.segments)


class OCRBackend(Protocol):
    """Contract for standard, stamp, or handwriting OCR implementations."""

    name: str

    def extract_page(self, page: fitz.Page, hint: OCRHint) -> OCRPageResult:
        """Return text recognized from one rendered PDF page."""


@dataclass
class TesseractOCRBackend:
    """
    Default OCR backend.

    It can often read clear numbers in a stamp or neat handwriting, but OCR
    results are deliberately always marked as requiring human verification.
    """

    language: str = "pol+eng"
    zoom: float = 2.0
    name: str = "Tesseract"

    def extract_page(self, page: fitz.Page, hint: OCRHint) -> OCRPageResult:
        try:
            import pytesseract
            from PIL import Image, ImageOps
        except ImportError as error:
            raise OCRUnavailableError(
                "OCR is not installed. Install Pillow and pytesseract first."
            ) from error

        matrix = fitz.Matrix(self.zoom, self.zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )

        image = ImageOps.autocontrast(image.convert("L"))
        config = "--oem 3 --psm 11" if hint is OCRHint.STAMP else "--oem 3 --psm 6"

        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=config,
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractNotFoundError as error:
            raise OCRUnavailableError(
                "The Tesseract application was not found. Install it and restart "
                "DocAuthorize."
            ) from error
        except pytesseract.TesseractError as error:
            raise OCRUnavailableError(
                "Tesseract could not run. Check that the Polish and English "
                f"language data are installed ({self.language})."
            ) from error

        lines: list[list[str]] = []
        current_line: tuple[int, int, int] | None = None
        for index, raw_word in enumerate(data["text"]):
            word = raw_word.strip()
            if not word:
                continue

            line_id = (
                int(data["block_num"][index]),
                int(data["par_num"][index]),
                int(data["line_num"][index]),
            )
            if line_id != current_line:
                lines.append([])
                current_line = line_id
            lines[-1].append(word)

        confidences = [
            float(value)
            for value in data["conf"]
            if value not in {"-1", ""} and float(value) >= 0
        ]
        confidence = sum(confidences) / len(confidences) if confidences else None

        return OCRPageResult(
            text="\n".join(" ".join(line) for line in lines),
            confidence=confidence,
        )


def process_pdf(
    file_path: str | Path,
    *,
    ocr_policy: OCRPolicy | str = OCRPolicy.FALLBACK,
    ocr_hints: Sequence[OCRHint | str] = (OCRHint.TEXT,),
    min_native_characters: int = 50,
    ocr_backend: OCRBackend | None = None,
) -> ProcessedPDF:
    """
    Extract text from a PDF and retain the provenance of every result.

    FALLBACK runs OCR only for pages with insufficient native text.  ALL_PAGES
    is intended for a second pass when a critical field, such as NIP, was not
    found in a digitally generated contract.
    """

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file was not found: {path}")

    policy = OCRPolicy(ocr_policy)
    hints = tuple(OCRHint(hint) for hint in ocr_hints)
    result = ProcessedPDF()
    backend = ocr_backend or TesseractOCRBackend()
    ocr_disabled = False

    try:
        document = fitz.open(path)
    except fitz.FileDataError as error:
        raise ValueError("The selected file is not a readable PDF.") from error

    try:
        for page_index, page in enumerate(document, start=1):
            native_text = page.get_text("text").strip()

            if native_text:
                result.segments.append(
                    TextSegment(
                        page_number=page_index,
                        text=native_text,
                        source=TextSource.PRINTED_TEXT,
                        requires_verification=False,
                    )
                )

            should_use_ocr = (
                policy is OCRPolicy.ALL_PAGES
                or not _has_sufficient_native_text(native_text, min_native_characters)
            )

            if not should_use_ocr or ocr_disabled:
                continue

            result.ocr_attempted = True
            for hint in hints:
                try:
                    ocr_result = backend.extract_page(page, hint)
                except OCRUnavailableError as error:
                    result.ocr_available = False
                    result.warnings.append(str(error))
                    ocr_disabled = True
                    break

                result.ocr_available = True
                if not ocr_result.text.strip():
                    continue

                result.segments.append(
                    TextSegment(
                        page_number=page_index,
                        text=ocr_result.text.strip(),
                        source=_source_for_hint(hint),
                        requires_verification=True,
                        confidence=ocr_result.confidence,
                    )
                )
    finally:
        document.close()

    if not result.segments:
        result.warnings.append("No readable text was found in this PDF.")

    return result


def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    Compatibility helper for code that previously expected a plain string.

    New code should call process_pdf() so it can show whether a value was
    obtained from printed text or OCR.
    """

    return process_pdf(file_path).text


def _has_sufficient_native_text(text: str, minimum: int) -> bool:
    return len(re.sub(r"\s+", "", text)) >= minimum


def _source_for_hint(hint: OCRHint) -> TextSource:
    if hint is OCRHint.HANDWRITING:
        return TextSource.HANDWRITING_OCR
    if hint is OCRHint.STAMP:
        return TextSource.STAMP_OCR
    return TextSource.OCR




#.