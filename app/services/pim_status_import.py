from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from app.repositories.pim_lifecycle_status_repository import PimLifecycleStatusRepository


_HEADER_ALIASES = {
    "itemno": "item_no",
    "itemnumber": "item_no",
    "item_no": "item_no",
    "articlenumber": "item_no",
    "artikelnummer": "item_no",
    "productlifecyclestatus": "lifecycle_status",
    "lifecycle_status": "lifecycle_status",
    "lifecyclestatus": "lifecycle_status",
    "productstatus": "lifecycle_status",
}

_NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_NS_REL = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
_SHEET_RELATIONSHIP_KEY = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


@dataclass(slots=True)
class PimStatusPreviewRow:
    item_no: str
    lifecycle_status: str
    is_visible: bool


@dataclass(slots=True)
class PimStatusParseResult:
    source_file_name: str
    total_rows: int
    importable_rows: int
    active_count: int
    other_status_count: int
    skipped_count: int
    preview_rows: list[PimStatusPreviewRow]
    rows_for_import: list[dict[str, str]]


class PimStatusImportService:
    def __init__(self, repository: PimLifecycleStatusRepository) -> None:
        self.repository = repository

    async def parse_upload(
        self,
        *,
        file_name: str | None,
        content: bytes,
        preview_limit: int = 10,
    ) -> PimStatusParseResult:
        normalized_file_name = (file_name or "upload").strip() or "upload"
        rows = self._load_rows(normalized_file_name, content)
        return self._normalize_rows(
            file_name=normalized_file_name,
            rows=rows,
            preview_limit=preview_limit,
        )

    async def import_rows(self, parsed: PimStatusParseResult) -> int:
        updated_at = datetime.now(timezone.utc)
        return await self.repository.bulk_upsert(
            parsed.rows_for_import,
            source_file_name=parsed.source_file_name,
            updated_at=updated_at,
        )

    def _load_rows(self, file_name: str, content: bytes) -> list[list[str]]:
        if not content:
            raise ValueError("Filen är tom.")

        suffix = Path(file_name).suffix.lower()
        if suffix == ".csv":
            return self._read_csv_rows(content)
        if suffix == ".xlsx":
            return self._read_xlsx_rows(content)
        raise ValueError("Endast .csv och .xlsx stöds för PIM Status Import.")

    def _normalize_rows(
        self,
        *,
        file_name: str,
        rows: list[list[str]],
        preview_limit: int,
    ) -> PimStatusParseResult:
        headers, data_rows = self._split_headers(rows)
        resolver = self._build_resolver(headers)

        missing = {"item_no", "lifecycle_status"} - set(resolver)
        if missing:
            raise ValueError(
                "Filen måste innehålla kolumnerna ItemNo och ProductLifeCycleStatus."
            )

        total_rows = 0
        active_count = 0
        other_status_count = 0
        skipped_count = 0
        preview_rows: list[PimStatusPreviewRow] = []
        deduped_rows: dict[str, dict[str, str]] = {}

        for raw_row in data_rows:
            if not any((value or "").strip() for value in raw_row):
                continue

            total_rows += 1
            item_no = self._normalize_text(self._value_at(raw_row, resolver["item_no"]))
            lifecycle_status = self._normalize_status(
                self._value_at(raw_row, resolver["lifecycle_status"])
            )

            if not item_no:
                skipped_count += 1
                continue

            is_visible = lifecycle_status == "active"
            if is_visible:
                active_count += 1
            else:
                other_status_count += 1

            if len(preview_rows) < preview_limit:
                preview_rows.append(
                    PimStatusPreviewRow(
                        item_no=item_no,
                        lifecycle_status=lifecycle_status,
                        is_visible=is_visible,
                    )
                )

            deduped_rows[item_no] = {
                "item_no": item_no,
                "lifecycle_status": lifecycle_status,
            }

        return PimStatusParseResult(
            source_file_name=file_name,
            total_rows=total_rows,
            importable_rows=len(deduped_rows),
            active_count=active_count,
            other_status_count=other_status_count,
            skipped_count=skipped_count,
            preview_rows=preview_rows,
            rows_for_import=list(deduped_rows.values()),
        )

    def _split_headers(self, rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
        for index, row in enumerate(rows):
            if any((value or "").strip() for value in row):
                headers = [self._normalize_text(value) for value in row]
                return headers, rows[index + 1 :]
        raise ValueError("Filen saknar rubrikrad.")

    def _build_resolver(self, headers: list[str]) -> dict[str, int]:
        resolver: dict[str, int] = {}
        for index, header in enumerate(headers):
            alias = _HEADER_ALIASES.get(self._normalize_header(header))
            if alias and alias not in resolver:
                resolver[alias] = index
        return resolver

    def _read_csv_rows(self, content: bytes) -> list[list[str]]:
        text = self._decode_text(content)
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(io.StringIO(text), dialect)
        return [[self._normalize_text(cell) for cell in row] for row in reader]

    def _read_xlsx_rows(self, content: bytes) -> list[list[str]]:
        try:
            workbook = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ValueError("Ogiltig XLSX-fil.") from exc

        with workbook:
            shared_strings = self._read_shared_strings(workbook)
            sheet_path = self._resolve_first_sheet_path(workbook)
            xml_root = ET.fromstring(workbook.read(sheet_path))

            rows: list[list[str]] = []
            for row_element in xml_root.findall(".//main:sheetData/main:row", _NS_MAIN):
                indexed_values: dict[int, str] = {}
                for cell in row_element.findall("main:c", _NS_MAIN):
                    reference = cell.attrib.get("r", "")
                    index = self._column_index(reference)
                    indexed_values[index] = self._read_cell_value(cell, shared_strings)
                if not indexed_values:
                    rows.append([])
                    continue
                width = max(indexed_values) + 1
                rows.append(
                    [self._normalize_text(indexed_values.get(i, "")) for i in range(width)]
                )
            return rows

    def _read_shared_strings(self, workbook: zipfile.ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in workbook.namelist():
            return []
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        shared_strings: list[str] = []
        for item in root.findall("main:si", _NS_MAIN):
            text_fragments = [node.text or "" for node in item.findall(".//main:t", _NS_MAIN)]
            shared_strings.append("".join(text_fragments))
        return shared_strings

    def _resolve_first_sheet_path(self, workbook: zipfile.ZipFile) -> str:
        workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
        relationships_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        relationship_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships_root.findall("rel:Relationship", _NS_REL)
        }
        first_sheet = workbook_root.find("main:sheets/main:sheet", _NS_MAIN)
        if first_sheet is None:
            raise ValueError("XLSX-filen saknar blad.")
        relationship_id = first_sheet.attrib.get(_SHEET_RELATIONSHIP_KEY)
        if not relationship_id or relationship_id not in relationship_map:
            raise ValueError("Kunde inte läsa första bladet i XLSX-filen.")
        target = relationship_map[relationship_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        return target

    def _read_cell_value(self, cell: ET.Element, shared_strings: list[str]) -> str:
        cell_type = cell.attrib.get("t")
        if cell_type == "s":
            value = cell.find("main:v", _NS_MAIN)
            if value is None or value.text is None:
                return ""
            try:
                return shared_strings[int(value.text)]
            except (IndexError, ValueError):
                return ""
        if cell_type == "inlineStr":
            return "".join(node.text or "" for node in cell.findall(".//main:t", _NS_MAIN))

        value = cell.find("main:v", _NS_MAIN)
        return value.text or "" if value is not None else ""

    def _column_index(self, reference: str) -> int:
        letters = "".join(char for char in reference if char.isalpha()).upper()
        if not letters:
            return 0
        index = 0
        for char in letters:
            index = (index * 26) + (ord(char) - 64)
        return max(index - 1, 0)

    def _decode_text(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Kunde inte läsa textinnehållet i filen.")

    def _normalize_header(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.strip().lower())

    def _normalize_text(self, value: str | None) -> str:
        return (value or "").strip()

    def _normalize_status(self, value: str | None) -> str:
        return self._normalize_text(value).lower()

    def _value_at(self, row: list[str], index: int) -> str:
        if index >= len(row):
            return ""
        return row[index]
