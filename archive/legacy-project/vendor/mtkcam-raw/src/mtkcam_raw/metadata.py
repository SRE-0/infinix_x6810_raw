"""
Android Camera2 metadata constants relevant to RAW enablement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Tags are constructed as: (page << 16) | section | tag_id
# ANDROID_REQUEST_AVAILABLE_CAPABILITIES = 0x000C000C
TAG_AVAILABLE_CAPABILITIES = 0x000C000C

# ANDROID_SCALER_AVAILABLE_STREAM_CONFIGURATIONS = 0x000D0012
TAG_AVAILABLE_STREAM_CONFIGURATIONS = 0x000D0012

# ANDROID_SENSOR_INFO_PIXEL_ARRAY_SIZE = 0x00120023
TAG_SENSOR_INFO_PIXEL_ARRAY_SIZE = 0x00120023

# ANDROID_SENSOR_INFO_ACTIVE_ARRAY_SIZE = 0x00120024
TAG_SENSOR_INFO_ACTIVE_ARRAY_SIZE = 0x00120024

TAG_NAMES: dict[int, str] = {
    0x000C000C: "ANDROID_REQUEST_AVAILABLE_CAPABILITIES",
    0x000D0012: "ANDROID_SCALER_AVAILABLE_STREAM_CONFIGURATIONS",
    0x00120023: "ANDROID_SENSOR_INFO_PIXEL_ARRAY_SIZE",
    0x00120024: "ANDROID_SENSOR_INFO_ACTIVE_ARRAY_SIZE",
}


BACKWARD_COMPATIBLE = 0
MANUAL_SENSOR = 1
MANUAL_POST_PROCESSING = 2
RAW = 3
PRIVATE_REPROCESSING = 4
READ_SENSOR_SETTINGS = 5
BURST_CAPTURE = 6
READ_SENSOR_SETTINGS_2 = 7
DEPTH_OUTPUT = 8
HIGH_SPEED_VIDEO = 9
CONSTRAINED_HIGH_SPEED_VIDEO = 10
MOTION_TRACKING = 11
LOGICAL_MULTI_CAMERA = 12
MONOCHROME = 13
SECURE_IMAGE_DATA = 14
SYSTEM_CAMERA = 15
OFFLINE_PROCESSING = 16
ULTRA_HIGH_RESOLUTION_SENSOR = 17
REMOSAIC_REPROCESSING = 18
DYNAMIC_RANGE_TEN_BIT = 19
STREAM_USE_CASE = 20
COLOR_SPACE_PROFILES = 21

CAP_NAMES: dict[int, str] = {
    0: "BACKWARD_COMPATIBLE",
    1: "MANUAL_SENSOR",
    2: "MANUAL_POST_PROCESSING",
    3: "RAW",
    4: "PRIVATE_REPROCESSING",
    5: "READ_SENSOR_SETTINGS",
    6: "BURST_CAPTURE",
    7: "READ_SENSOR_SETTINGS_2",
    8: "DEPTH_OUTPUT",
    9: "HIGH_SPEED_VIDEO",
    10: "CONSTRAINED_HIGH_SPEED_VIDEO",
    11: "MOTION_TRACKING",
    12: "LOGICAL_MULTI_CAMERA",
    13: "MONOCHROME",
    14: "SECURE_IMAGE_DATA",
    15: "SYSTEM_CAMERA",
    16: "OFFLINE_PROCESSING",
    17: "ULTRA_HIGH_RESOLUTION_SENSOR",
    18: "REMOSAIC_REPROCESSING",
    19: "DYNAMIC_RANGE_TEN_BIT",
    20: "STREAM_USE_CASE",
    21: "COLOR_SPACE_PROFILES",
}

CAP_NAME_TO_VALUE: dict[str, int] = {
    v: k for k, v in CAP_NAMES.items()
}


def cap_name(value: int) -> str:
    return CAP_NAMES.get(value, f"CAP_{value}")


def tag_name(tag: int) -> str:
    return TAG_NAMES.get(tag, f"TAG_0x{tag:08x}")


HAL_PIXEL_FORMAT_RAW16 = 32
HAL_PIXEL_FORMAT_RAW10 = 37
HAL_PIXEL_FORMAT_RAW12 = 38
HAL_PIXEL_FORMAT_YUV = 33  # YCbCr_420_888
HAL_PIXEL_FORMAT_BLOB = 34  # JPEG
HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED = 34

FORMAT_NAMES: dict[int, str] = {
    32: "RAW16",
    37: "RAW10",
    38: "RAW12",
    33: "YUV_420_888",
    34: "BLOB",
    35: "YCbCr_422_I",
    36: "YCbCr_420_SP",
    39: "Y16",
}

FORMAT_NAME_TO_VALUE: dict[str, int] = {
    v: k for k, v in FORMAT_NAMES.items()
}


def resolve_format(value: str | int) -> int:
    if isinstance(value, int):
        return value
    upper = value.upper()
    if upper in FORMAT_NAME_TO_VALUE:
        return FORMAT_NAME_TO_VALUE[upper]
    if upper.startswith("0X") or upper.isdigit():
        return int(upper, 0)
    raise ValueError(f"Unknown format: {value}")


@dataclass
class StreamEntry:
    width: int
    height: int
    format: int = 32  # HAL_PIXEL_FORMAT_RAW16
    direction: int = 0  # STREAM_DIRECTION_OUTPUT
    hal_pixel_format: Optional[int] = None
    override_format: Optional[int] = None

    def to_tuple(
        self,
        hal_format_meta: Optional[dict[int, tuple[int, int]]] = None,
    ) -> tuple[int, ...]:
        if hal_format_meta is None:
            hal_format_meta = {}
        hpf = self.hal_pixel_format
        ovf = self.override_format
        if hpf is None or ovf is None:
            defaults = hal_format_meta.get(self.format)
            if defaults:
                if hpf is None:
                    hpf = defaults[0]
                if ovf is None:
                    ovf = defaults[1]
            else:
                if hpf is None:
                    hpf = 0
                if ovf is None:
                    ovf = self.format
        return (self.format, self.width, self.height, self.direction, hpf, ovf)


def stream_entry_from_dict(d: dict) -> StreamEntry:
    kwargs: dict = {}

    raw_fmt = d.get("format", 32)
    kwargs["format"] = resolve_format(raw_fmt)

    raw_dir = d.get("direction", 0)
    if isinstance(raw_dir, str):
        upper = raw_dir.upper().strip()
        if upper == "OUTPUT":
            kwargs["direction"] = 0
        elif upper == "INPUT":
            kwargs["direction"] = 1
        else:
            kwargs["direction"] = int(raw_dir, 0)
    else:
        kwargs["direction"] = raw_dir

    kwargs["width"] = int(d["width"])
    kwargs["height"] = int(d["height"])

    if "hal_pixel_format" in d:
        kwargs["hal_pixel_format"] = int(str(d["hal_pixel_format"]), 0)
    if "override_format" in d:
        kwargs["override_format"] = int(str(d["override_format"]), 0)

    return StreamEntry(**kwargs)


STREAM_DIRECTION_OUTPUT = 0
STREAM_DIRECTION_INPUT = 1

DIRECTION_NAMES: dict[int, str] = {
    0: "OUTPUT",
    1: "INPUT",
}


def is_submode(
    sensor_name: str,
    skip_suffixes: tuple[str, ...] = ("_securecamera",),
) -> bool:
    lower = sensor_name.lower()
    return any(lower.endswith(sfx.lower()) for sfx in skip_suffixes)


def sensor_short_name(
    sym_name: str,
    prefix: str = "constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_",
) -> str:
    if sym_name.startswith(prefix):
        return sym_name[len(prefix):]
    return sym_name
