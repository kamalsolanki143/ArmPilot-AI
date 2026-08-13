"""
ArmPilot-AI — PerformiX Output Parser
Parses raw ARM PerformiX benchmark output into structured data.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.core.logger import logger


class PerformixParser:
    """Parses text output from ARM PerformiX benchmark runs."""

    # Common patterns in PerformiX output
    _PATTERNS = {
        "metric_line": re.compile(
            r"^\s*(?P<category>\w[\w\s]*?):\s*(?P<metric>[\w_]+)\s*=\s*(?P<value>[\d.]+)\s*(?P<unit>\w*)",
            re.MULTILINE,
        ),
        "kv_pair": re.compile(
            r"(?P<key>[\w_]+)\s*[=:]\s*(?P<value>[\d.]+)",
        ),
        "section_header": re.compile(
            r"^\s*[=\-]{3,}\s*(?P<title>[\w\s]+?)\s*[=\-]{3,}\s*$",
            re.MULTILINE,
        ),
        "summary_block": re.compile(
            r"(?i)summary|results|overview",
            re.MULTILINE,
        ),
    }

    def parse(self, raw_output: str) -> dict[str, Any]:
        """Parse raw PerformiX output into a structured dictionary."""
        if not raw_output or not raw_output.strip():
            return {"sections": [], "metrics": {}, "raw_length": 0}

        result: dict[str, Any] = {
            "sections": [],
            "metrics": {},
            "summary": {},
            "raw_length": len(raw_output),
            "parse_errors": [],
        }

        try:
            sections = self._extract_sections(raw_output)
            result["sections"] = sections

            metrics = self._extract_metrics(raw_output)
            result["metrics"] = metrics

            summary = self._extract_summary(raw_output)
            result["summary"] = summary

            logger.info(
                "Parsed PerformiX output: %d sections, %d metrics",
                len(sections), len(metrics),
            )

        except Exception as e:
            result["parse_errors"].append(str(e))
            logger.error("Failed to parse PerformiX output: %s", e)

        return result

    def _extract_sections(self, text: str) -> list[dict[str, Any]]:
        """Extract named sections from the output."""
        sections: list[dict[str, Any]] = []
        matches = list(self._PATTERNS["section_header"].finditer(text))

        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            sections.append({
                "title": match.group("title").strip(),
                "content": content,
                "line_offset": text[:match.start()].count("\n") + 1,
            })

        return sections

    def _extract_metrics(self, text: str) -> dict[str, Any]:
        """Extract all metric key-value pairs."""
        metrics: dict[str, Any] = {}

        # Pattern: category: metric = value unit
        for match in self._PATTERNS["metric_line"].finditer(text):
            category = match.group("category").strip()
            metric = match.group("metric").strip()
            value = self._parse_number(match.group("value"))
            unit = match.group("unit").strip() or None

            if category not in metrics:
                metrics[category] = {}
            metrics[category][metric] = {
                "value": value,
                "unit": unit,
            }

        # Fallback: generic key=value pairs
        if not metrics:
            for match in self._PATTERNS["kv_pair"].finditer(text):
                key = match.group("key").strip()
                value = self._parse_number(match.group("value"))
                if key not in metrics:
                    metrics[key] = {"value": value}

        return metrics

    def _extract_summary(self, text: str) -> dict[str, Any]:
        """Extract the summary or overview section."""
        lines = text.split("\n")
        summary_lines: list[str] = []
        in_summary = False

        for line in lines:
            if self._PATTERNS["summary_block"].search(line):
                in_summary = True
                continue
            if in_summary:
                if line.strip() == "" and summary_lines:
                    break
                if line.strip():
                    summary_lines.append(line.strip())

        summary: dict[str, Any] = {}
        for line in summary_lines:
            match = self._PATTERNS["kv_pair"].search(line)
            if match:
                key = match.group("key").strip()
                value = self._parse_number(match.group("value"))
                summary[key] = value
            elif ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                val = val.strip()
                try:
                    summary[key] = float(val)
                except ValueError:
                    summary[key] = val

        return summary

    def extract_single_metric(
        self,
        raw_output: str,
        metric_name: str,
    ) -> Optional[float]:
        """Extract a single metric value by name."""
        for match in self._PATTERNS["kv_pair"].finditer(raw_output):
            if match.group("key").strip().lower() == metric_name.lower():
                return self._parse_number(match.group("value"))

        for match in self._PATTERNS["metric_line"].finditer(raw_output):
            if match.group("metric").strip().lower() == metric_name.lower():
                return self._parse_number(match.group("value"))

        return None

    @staticmethod
    def _parse_number(value: str) -> float:
        """Parse a numeric string value."""
        try:
            return float(value)
        except ValueError:
            return 0.0


# Singleton
performix_parser = PerformixParser()
