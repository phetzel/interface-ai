"""Local pixel recognition primitives; no model or application-state access."""

from .primitives import Box, Match, VisionError, find_matches, unique_match
from .ocr import OCR, parse_usd

__all__ = ['Box', 'Match', 'VisionError', 'find_matches', 'unique_match', 'OCR', 'parse_usd']
