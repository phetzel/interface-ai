from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from PIL import Image
from pydantic import ValidationError
from interface_ai.contracts.models import Capability, MemberInput


class ReplayError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Bundle:
    capability: Capability
    sha256: str
    templates: dict


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError('Non-finite JSON number')

    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid_constant)


def load_bundle(path):
    try:
        path = Path(path).resolve(strict=True)
        if path.stat().st_size > 262144:
            raise ValueError('Oversized artifact')
        raw = path.read_bytes()
        capability = Capability.model_validate(strict_json(raw))
    except (OSError, ValueError, RecursionError):
        raise ReplayError(
            'invalid_capability', 'Capability JSON or semantic validation failed'
        ) from None
    templates = {}
    for name, asset in capability.assets.items():
        try:
            asset_path = (path.parent / asset.file).resolve(strict=True)
            if not asset_path.is_relative_to(path.parent) or asset_path.stat().st_size > 131072:
                raise ValueError('Invalid asset location or size')
            if hashlib.sha256(asset_path.read_bytes()).hexdigest() != asset.sha256:
                raise ValueError('Asset digest mismatch')
            with Image.open(asset_path) as image:
                if image.format != 'PNG' or not (
                    3 <= image.width <= 512 and 3 <= image.height <= 256
                ):
                    raise ValueError('Unsupported anchor image')
                templates[name] = image.convert('RGB')
        except (OSError, ValueError):
            raise ReplayError(
                'invalid_asset', 'An anchor is missing, altered, or outside the bundle'
            ) from None
    return Bundle(capability, hashlib.sha256(raw).hexdigest(), templates)


def validate_inputs(data):
    try:
        return MemberInput.model_validate(data)
    except ValidationError:
        raise ReplayError(
            'invalid_input', 'Input must match the declared member-ID contract'
        ) from None
