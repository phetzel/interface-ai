from dataclasses import dataclass
import math

import cv2
import numpy as np

cv2.setNumThreads(1)


class VisionError(RuntimeError):
    def __init__(self, code, message, **details):
        self.code, self.details = code, details
        super().__init__(message)


@dataclass(frozen=True)
class Box:
    left: int
    top: int
    right: int
    bottom: int

    def checked(self, size):
        if (
            any(type(v) is not int for v in self.tuple())
            or not 0 <= self.left < self.right <= size[0]
            or not 0 <= self.top < self.bottom <= size[1]
        ):
            raise VisionError('invalid_region', 'Region must be fully inside the screenshot')
        return self

    def tuple(self):
        return self.left, self.top, self.right, self.bottom

    @property
    def center(self):
        return (self.left + self.right) // 2, (self.top + self.bottom) // 2

    def relative(self, offsets, size):
        x1, y1, x2, y2 = offsets
        return Box(self.left + x1, self.top + y1, self.left + x2, self.top + y2).checked(size)


@dataclass(frozen=True)
class Match:
    box: Box
    score: float


def find_matches(image, template, region=None, *, threshold=0.92):
    if (
        type(threshold) not in (int, float)
        or not math.isfinite(threshold)
        or not 0.5 <= threshold <= 1
    ):
        raise VisionError('invalid_threshold', 'Match threshold must be between 0.5 and 1')
    region = (region or Box(0, 0, *image.size)).checked(image.size)
    source = np.asarray(image.crop(region.tuple()).convert('L'))
    anchor = np.asarray(template.convert('L'))
    height, width = anchor.shape
    if min(width, height) < 3 or float(anchor.std()) < 5:
        raise VisionError('invalid_anchor', 'Anchor must contain distinctive pixel variation')
    if width > source.shape[1] or height > source.shape[0]:
        raise VisionError('invalid_region', 'Search region is smaller than the anchor')
    scores = cv2.matchTemplate(source, anchor, cv2.TM_CCOEFF_NORMED)
    # Group neighboring above-threshold placements of the same visual occurrence.
    # Keep every distinct cluster; never silently select the highest of duplicates.
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (scores >= threshold).astype(np.uint8), 8
    )
    matches = []
    if count > 65:
        raise VisionError(
            'ambiguous_target', 'Too many visual candidates', candidateCount=count - 1
        )
    for label in range(1, count):
        x, y, w, h, _ = stats[label]
        local = np.where(labels[y : y + h, x : x + w] == label, scores[y : y + h, x : x + w], -1)
        dy, dx = np.unravel_index(np.argmax(local), local.shape)
        left, top = region.left + int(x + dx), region.top + int(y + dy)
        matches.append(Match(Box(left, top, left + width, top + height), float(local[dy, dx])))
    return sorted(matches, key=lambda match: (match.box.top, match.box.left))


def unique_match(image, template, region=None, *, threshold=0.92):
    matches = find_matches(image, template, region, threshold=threshold)
    if not matches:
        raise VisionError('target_missing', 'Visual target was not found', candidateCount=0)
    if len(matches) != 1:
        raise VisionError(
            'ambiguous_target', 'Visual target is not unique', candidateCount=len(matches)
        )
    return matches[0]
