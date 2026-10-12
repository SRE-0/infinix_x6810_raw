"""
Device definitions — one config object per supported device.

Adding support for a new device requires editing only this file:
create a new ``DeviceConfig`` entry and register it.  The patching
engine reads every offset and parameter from the device config.

Architecture
------------
``DeviceConfig``
    Immutable (frozen) container for everything specific to one
    device/binary.

    ``identity``
        Binary identification for compatibility checking.

    ``sensors``
        Declarative list of ``SensorConfig`` — one per physical
        sensor on the device.

    ``patches``
        ``PatchSet`` grouping structural patch definitions.

    ``quirks``
        Set of ``DeviceQuirk`` enum values — typed feature flags
        that never suffer from typos.

    ``validate_library(data)``
        Self-test returning ``list[ValidationIssue]``.  Empty list
        means all checks passed.

Signature resolution
--------------------
Each ``PatchDef`` carries a ``ByteSignature`` that is scanned at
runtime.  ``DeviceConfig.resolve_offset(data, sig)`` finds the patch
site.  An absolute ``fallback_offset`` is used only when the
signature is not found.

::

    ByteSignature.resolve(data) -> Optional[int]
        Scans *data* for the pattern, optionally applying mask.
        Raises ``SignatureAmbiguous`` when more than one match is
        found (unless ``allow_multiple=True``).

    DeviceConfig.resolve_offset(data, sig, cache=None)
        Like ``ByteSignature.resolve`` but also consults/updates a
        caller-provided ``dict`` cache so repeated lookups do not
        rescan the binary.

Porting workflow
----------------
1.  Add a ``DeviceConfig(...)`` to this file.
2.  Add ``ByteSignature`` patterns (or verified ``fallback_offset``).
3.  ``mtkcam-raw validate lib.so`` — fix issues.
4.  ``mtkcam-raw --validate patch lib.so``
5.  ``mtkcam-raw verify orig.so patched.so``

Compatibility matrix (tested device / binary combinations)
----------------------------------------------------------
Device         Library version  SHA-256 (first 12)        Android  Status
INOI_A75       stock            aee927b9c8a5              Android 14  ✓ validated
ADVAN_X1       stock            b72c2eea9e84              Android 14  ✓ validated
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Optional


# ============================================================================
# Schema / patch versioning
# ============================================================================

SCHEMA_VERSION = "1.0"  # bump on breaking changes to device definition format
PATCH_VERSION = "1.0"   # bump on breaking changes to patch layout


# ============================================================================
# Typed quirk flags
# ============================================================================


class DeviceQuirk(Enum):
    """Feature flags that modify patching behaviour.

    Add new quirks here as the project grows — never use
    string literals in device definitions.
    """
    FORCE_LEVEL_3 = auto()             # force LEVEL_3 even if already available
    SKIP_FRONT_RAW = auto()            # do not add RAW capability to front sensors
    NO_RAW16 = auto()                  # skip RAW16 stream entry addition


# ============================================================================
# Signature resolution
# ============================================================================


class SignatureAmbiguous(ValueError):
    """Raised when a ``ByteSignature`` matches more than one location."""

    def __init__(
        self, sig: ByteSignature, matches: list[int]
    ) -> None:
        self.sig = sig
        self.matches = matches
        super().__init__(
            f"Signature '{sig.description}' matched {len(matches)} locations: "
            + ", ".join(f"0x{m:x}" for m in matches)
        )


@dataclass(frozen=True)
class ByteSignature:
    """Byte pattern used to locate a patch site at runtime.

    The patcher scans the binary for ``pattern`` (with optional
    ``mask`` applied via ``byte & mask == pattern``), then adds
    ``offset_from_match`` to get the final file offset.

    A mask of ``None`` means exact match.
    By default, a single match is required — multiple matches
    raise ``SignatureAmbiguous``.  Set ``allow_multiple=True``
    to accept the first match silently.
    """

    pattern: bytes
    mask: Optional[bytes] = None
    offset_from_match: int = 0
    description: str = ""
    allow_multiple: bool = False

    def __post_init__(self) -> None:
        if self.mask is not None and len(self.mask) != len(self.pattern):
            raise ValueError(
                f"mask length ({len(self.mask)}) must match "
                f"pattern length ({len(self.pattern)})"
            )

    def resolve(self, data: bytes) -> Optional[int]:
        """Scan *data* and return the resolved file offset.

        Returns ``None`` when the signature is not found.
        Raises ``SignatureAmbiguous`` when more than one match
        is found and ``allow_multiple`` is ``False``.
        """
        matches: list[int] = []
        if self.mask is not None:
            for i in range(len(data) - len(self.pattern)):
                match = True
                for j in range(len(self.pattern)):
                    if (data[i + j] & self.mask[j]) != self.pattern[j]:
                        match = False
                        break
                if match:
                    matches.append(i + self.offset_from_match)
                    if self.allow_multiple:
                        return matches[0]
        else:
            pos = 0
            while True:
                idx = data.find(self.pattern, pos)
                if idx < 0:
                    break
                matches.append(idx + self.offset_from_match)
                if self.allow_multiple:
                    return matches[0]
                pos = idx + 1

        if not matches:
            return None
        if len(matches) > 1 and not self.allow_multiple:
            raise SignatureAmbiguous(self, matches)
        return matches[0]


# ============================================================================
# Patch definitions
# ============================================================================


@dataclass(frozen=True)
class PatchDef:
    """One atomic byte-range change with validation data.

    ``signature``
        How to find this patch site in the binary.
    ``old_bytes``
        Expected bytes before patching.
    ``new_bytes``
        Replacement bytes to write.
    ``fallback_offset``
        Absolute file offset used when ``signature`` is not found
        (``None`` = error out if signature resolution fails).
    """

    name: str
    signature: ByteSignature
    old_bytes: bytes
    new_bytes: bytes
    fallback_offset: Optional[int] = None
    patch_version: str = PATCH_VERSION


@dataclass(frozen=True)
class PatchSet:
    """Container for all structural patch definitions."""

    hwlevel: Optional[PatchDef] = None
    cave_signature: Optional[ByteSignature] = None
    patch_version: str = PATCH_VERSION


# ============================================================================
# Sensor configuration
# ============================================================================


@dataclass(frozen=True)
class SensorConfig:
    """Declarative description of one physical sensor on the device.

    ``prefix``
        Name substring used to match against the symbol short name
        (e.g. ``"IMX686"`` matches ``IMX686_MIPI_RAW``).
    ``role``
        Semantic role — one of ``"back"``, ``"front"``, ``"depth"``,
        ``"macro"``, ``"wide"``, ``"unknown"``.
    ``priority``
        Lower number = patched first.  Sensors with priority < 999
        are considered "main" and always get full desired capabilities.
    ``raw_enabled``
        Whether to add RAW capability + RAW16 stream entry for this
        sensor.
    ``stream_entries``
        Per-sensor stream entries override.  ``None`` means fall
        back to ``DeviceConfig.default_stream_entries``.
    """

    prefix: str
    role: str = "unknown"
    priority: int = 999
    raw_enabled: bool = True
    stream_entries: Optional[list[tuple[int, ...]]] = None


# ============================================================================
# Device identity
# ============================================================================


@dataclass(frozen=True)
class DeviceIdentity:
    """Binary identification for compatibility checking.

    At least one field should be set so that ``validate_library``
    can confirm the correct binary is being patched.
    """

    build_fingerprint: Optional[str] = None
    library_sha256: Optional[str] = None
    library_size: Optional[int] = None
    supported_versions: list[str] = field(default_factory=list)


# ============================================================================
# Structured validation
# ============================================================================


class IssueSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    """One issue reported by ``DeviceConfig.validate_library``."""

    severity: IssueSeverity
    code: str
    message: str
    offset: Optional[int] = None

    def __str__(self) -> str:
        prefix = {
            IssueSeverity.ERROR: "[ERROR]",
            IssueSeverity.WARNING: "[WARN]",
            IssueSeverity.INFO: "[INFO]",
        }[self.severity]
        off = f" @0x{self.offset:x}" if self.offset is not None else ""
        return f"{prefix} {self.code}{off}: {self.message}"


# ============================================================================
# Top-level device configuration
# ============================================================================

SENSOR_PREFIX = (
    "constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_"
)

STREAM_ENTRY_DEFAULT = (32, 640, 480, 0, 0x3F940AA, 0x1FCA055)

HAL_FORMAT_META_DEFAULT: dict[int, tuple[int, int]] = {
    32: (0x3F940AA, 0x1FCA055),  # RAW16
}

CAP_TIER_DEFAULT = [
    "RAW",
    "MANUAL_POST_PROCESSING",
    "PRIVATE_REPROCESSING",
    "READ_SENSOR_SETTINGS_2",
    "HIGH_SPEED_VIDEO",
]

SKIP_SUFFIXES_DEFAULT: tuple[str, ...] = (
    "_securecamera", "_bayermono", "_bayerbayer", "_bayerwide",
    "_dummy", "_satcam", "_vsdof", "_lvsdof", "_fvsdof",
    "_dualzoom", "_tricam", "_trivsdof", "_trizvsdof",
    "_staggerTriZoom", "_staggerZoom",
)


@dataclass(frozen=True)
class DeviceConfig:
    """All device-specific parameters for patching ``libmtkcam_metastore.so``.

    Every field has a sensible default — set only what differs from
    the generic MediaTek HAL convention.

    **Immutable** — use ``with_main_sensors()`` to obtain a modified
    copy with adjusted sensor priorities.
    """

    # ── Versioning ────────────────────────────────────────────────────
    schema_version: str = SCHEMA_VERSION

    # ── Identity ──────────────────────────────────────────────────────
    name: str = ""
    soc: str = ""
    identity: DeviceIdentity = field(default_factory=DeviceIdentity)

    # ── Symbol scan ───────────────────────────────────────────────────
    sensor_prefix: str = SENSOR_PREFIX

    # ── Sensors ───────────────────────────────────────────────────────
    sensors: tuple[SensorConfig, ...] = field(default_factory=tuple)

    # ── HAL metadata ──────────────────────────────────────────────────
    hal_format_meta: dict[int, tuple[int, int]] = field(
        default_factory=lambda: dict(HAL_FORMAT_META_DEFAULT)
    )

    # ── Structural patches ────────────────────────────────────────────
    patches: PatchSet = field(default_factory=PatchSet)

    # ── Cave / trampoline ─────────────────────────────────────────────
    plt_cave_va: int = 0

    # ── Capability tier (ordered) ────────────────────────────────────
    desired_cap_tier: tuple[str, ...] = field(
        default_factory=lambda: tuple(CAP_TIER_DEFAULT)
    )

    # ── Default stream entries ────────────────────────────────────────
    default_stream_entries: tuple[tuple[int, ...], ...] = field(
        default_factory=lambda: (STREAM_ENTRY_DEFAULT,)
    )

    # ── Sensor filtering ──────────────────────────────────────────────
    skip_suffixes: tuple[str, ...] = SKIP_SUFFIXES_DEFAULT

    # ── Typed quirks ──────────────────────────────────────────────────
    quirks: frozenset[DeviceQuirk] = field(default_factory=frozenset)

    # ===================================================================
    # Resolution helpers
    # ===================================================================

    def resolve_offset(
        self,
        data: bytes,
        sig: ByteSignature,
        cache: Optional[dict[int, int]] = None,
    ) -> Optional[int]:
        """Resolve *sig* against *data*, with optional *cache*.

        When *cache* is provided (a ``dict`` keyed by ``id(sig)``),
        repeated lookups for the same signature object return the
        cached result without rescanning.
        """
        if cache is not None:
            sig_id = id(sig)
            try:
                return cache[sig_id]
            except KeyError:
                pass
        result = sig.resolve(data)
        if cache is not None:
            cache[sig_id] = result
        return result

    def resolve_patch_offset(
        self,
        data: bytes,
        patch: PatchDef,
        cache: Optional[dict[int, int]] = None,
    ) -> Optional[int]:
        """Resolve the file offset for *patch* using signature first.

        Falls back to ``patch.fallback_offset`` if the signature scan
        returns nothing.
        """
        off = self.resolve_offset(data, patch.signature, cache)
        if off is not None:
            return off
        return patch.fallback_offset

    # ===================================================================
    # Sensor helpers
    # ===================================================================

    def find_sensor(self, short_name: str) -> Optional[SensorConfig]:
        """Return the first ``SensorConfig`` matching *short_name*."""
        for s in self.sensors:
            if s.prefix.upper() in short_name.upper():
                return s
        return None

    def get_priority(self, short_name: str) -> int:
        s = self.find_sensor(short_name)
        return s.priority if s else 999

    def is_main_sensor(self, short_name: str) -> bool:
        s = self.find_sensor(short_name)
        return s is not None and s.priority < 999

    def stream_entries_for(
        self,
        sensor_name: str,
        config_overrides: Optional[dict[str, list[str]]] = None,
    ) -> list[tuple[int, ...]]:
        """Resolve stream entries for *sensor_name*.

        Priority:
          1. ``config_overrides`` (from TOML) — substring match key.
          2. Per-sensor ``SensorConfig.stream_entries``.
          3. ``default_stream_entries``.
        """
        if config_overrides:
            from mtkcam_raw.trampoline import parse_stream_entries
            for sens, entries in config_overrides.items():
                if sens.upper() in sensor_name.upper():
                    parsed = parse_stream_entries(entries)
                    if parsed:
                        return parsed
        sc = self.find_sensor(sensor_name)
        if sc is not None and sc.stream_entries is not None:
            return list(sc.stream_entries)
        return list(self.default_stream_entries)

    def with_main_sensors(self, overrides: list[str]) -> DeviceConfig:
        """Return a copy with sensor priorities adjusted by *overrides*.

        Only sensors whose prefix matches an override string get
        updated priorities (0, 1, 2, …).  All other sensors keep
        their original priority.
        """
        new_sensors: list[SensorConfig] = []
        for sc in self.sensors:
            matched_idx: Optional[int] = None
            for i, m in enumerate(overrides):
                if m.upper() in sc.prefix.upper() and (
                    matched_idx is None or i < matched_idx
                ):
                    matched_idx = i
            if matched_idx is not None:
                new_sensors.append(replace(sc, priority=matched_idx))
            else:
                new_sensors.append(sc)
        return replace(self, sensors=tuple(new_sensors))

    # ===================================================================
    # Validation
    # ===================================================================

    def validate_library(self, data: bytes) -> list[ValidationIssue]:
        """Run self-tests on *data* (a loaded ELF binary).

        Returns a list of ``ValidationIssue`` objects.
        An empty list means all checks passed.
        """
        issues: list[ValidationIssue] = []

        # ── Identity checks ──────────────────────────────────────────
        ident = self.identity
        if ident.library_size is not None and len(data) != ident.library_size:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="SIZE_MISMATCH",
                message=(
                    f"Expected {ident.library_size} bytes, "
                    f"got {len(data)}"
                ),
            ))
        if ident.library_sha256 is not None:
            actual = hashlib.sha256(data).hexdigest()
            if actual != ident.library_sha256:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    code="SHA256_MISMATCH",
                    message=(
                        f"Expected {ident.library_sha256}, "
                        f"got {actual}"
                    ),
                ))

        # ── ELF structure ────────────────────────────────────────────
        from mtkcam_raw.verify import validate_elf_structure
        for err in validate_elf_structure(data):
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="ELF_INVALID",
                message=err,
            ))

        # ── Patch signature resolution + old_bytes verification ──────
        from mtkcam_raw.elf import parse_elf

        cache: dict[int, Optional[int]] = {}

        if self.patches.hwlevel is not None:
            hp = self.patches.hwlevel
            try:
                off = self.resolve_patch_offset(data, hp, cache)
            except SignatureAmbiguous as exc:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    code="HWLEVEL_AMBIGUOUS",
                    message=str(exc),
                ))
                off = None

            if off is not None:
                actual = data[off:off + len(hp.old_bytes)]
                if actual != hp.old_bytes:
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        code="HWLEVEL_BYTES_MISMATCH",
                        message=(
                            f"At resolved offset 0x{off:x}: "
                            f"found {actual.hex()}, "
                            f"expected {hp.old_bytes.hex()}"
                        ),
                        offset=off,
                    ))
            elif hp.fallback_offset is not None:
                fallback = hp.fallback_offset
                actual = data[fallback:fallback + len(hp.old_bytes)]
                if actual != hp.old_bytes:
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        code="HWLEVEL_FALLBACK_BYTES_MISMATCH",
                        message=(
                            f"At fallback offset 0x{fallback:x}: "
                            f"found {actual.hex()}, "
                            f"expected {hp.old_bytes.hex()}"
                        ),
                        offset=fallback,
                    ))
            else:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    code="HWLEVEL_SIGNATURE_NOT_FOUND",
                    message=(
                        "hwlevel signature not found and no "
                        "fallback_offset provided"
                    ),
                ))

        # ── Cave availability ────────────────────────────────────────
        try:
            image = parse_elf(data)
        except ValueError as e:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="ELF_PARSE_FAILED",
                message=str(e),
            ))
            return issues

        from mtkcam_raw.cave import (
            find_plt_cave,
            find_load12_gap,
            find_load2_end_extension,
        )

        plt_cave = find_plt_cave(image)
        gap = find_load12_gap(image)
        ext = find_load2_end_extension(image)

        if self.plt_cave_va > 0:
            if plt_cave is not None:
                if plt_cave.size < 32:
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        code="PLT_CAVE_TOO_SMALL",
                        message=(
                            f"PLT cave is {plt_cave.size}B; "
                            f"minimum recommended is 32B"
                        ),
                        offset=plt_cave.file_offset,
                    ))
            else:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    code="PLT_CAVE_NOT_FOUND",
                    message="No PLT code cave discovered",
                ))

        if gap is not None:
            if gap.size < 256:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    code="GAP_CAVE_TOO_SMALL",
                    message=(
                        f"Gap cave is {gap.size}B; "
                        f"minimum recommended is 256B"
                    ),
                    offset=gap.file_offset,
                ))
        else:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="GAP_CAVE_NOT_FOUND",
                message="No LOAD1-LOAD2 gap cave discovered",
            ))

        if ext is None or ext.size < 64:
            avail = ext.size if ext else 0
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="END_CAVE_INSUFFICIENT",
                message=(
                    f"End-of-LOAD2 cave is {avail}B; "
                    f"minimum recommended is 64B"
                ),
                offset=ext.file_offset if ext else None,
            ))

        return issues


# ============================================================================
# Registry
# ============================================================================

DEVICES: dict[str, DeviceConfig] = {}


def _register(cfg: DeviceConfig) -> DeviceConfig:
    DEVICES[cfg.name.upper()] = cfg
    return cfg


def get_device(name: str) -> DeviceConfig:
    key = name.strip().upper().replace("-", "_")
    if key in DEVICES:
        return DEVICES[key]
    raise KeyError(
        f"Unknown device: {name}. Available: "
        + ", ".join(sorted(DEVICES))
    )


# ============================================================================
# Device definitions
# ============================================================================

# -- INOI A75 (stock MediaTek reference) -------------------------------------

INOI_A75 = _register(DeviceConfig(
    name="INOI_A75",
    soc="MT6789",
    identity=DeviceIdentity(
        library_sha256="aee927b9c8a5d7908a296bf9199eb0c45704e7cd6468538c56a42bdddb73e883",
        library_size=712440,
    ),
    sensors=(
        SensorConfig(prefix="S5KJN1", role="back", priority=0, raw_enabled=True),
        SensorConfig(prefix="S5K3L6", role="front", priority=1, raw_enabled=True),
        SensorConfig(prefix="BF2257", role="back", priority=2, raw_enabled=True),
        SensorConfig(prefix="BF20A1", role="front", priority=3, raw_enabled=True),
    ),
    patches=PatchSet(
        hwlevel=PatchDef(
            name="hwlevel: force LEVEL_3 (csel ne → al)",
            signature=ByteSignature(
                pattern=bytes.fromhex("13119f1a"),
                description="csel w19, w8, wzr, ne in updateHardwareLevel",
            ),
            old_bytes=bytes.fromhex("13119f1a"),
            new_bytes=bytes.fromhex("13e19f1a"),
            fallback_offset=0x77EE4,
        ),
    ),
    plt_cave_va=0xAB064,
))

# -- ADVAN X1 ----------------------------------------------------------------
# LOAD layout:
#   LOAD[1]=R  off=0x0      va=0x0      fz=0x421b4
#   LOAD[2]=RE off=0x43000  va=0x43000  fz=0xcae90
#   LOAD[3]=RW off=0x10e000 va=0x10e000 fz=0x10f0
#   LOAD[4]=RW off=0x10f0f0 va=0x1100f0 fz=0xfc

ADVAN_X1 = _register(DeviceConfig(
    name="ADVAN_X1",
    soc="MT6789",
    identity=DeviceIdentity(
        library_sha256="b72c2eea9e840f90348501e4c493c490a84fbde589d79f480edcfbe11a53c0eb",
        library_size=1114184,
    ),
    sensors=(
        SensorConfig(prefix="IMX686", role="back", priority=0, raw_enabled=True),
        SensorConfig(prefix="GC08A3", role="front", priority=1, raw_enabled=True),
        SensorConfig(prefix="IMX782", role="back", priority=2, raw_enabled=True),
    ),
    patches=PatchSet(
        hwlevel=PatchDef(
            name="hwlevel: force LEVEL_3 (csel ne → al)",
            signature=ByteSignature(
                pattern=bytes.fromhex("13119f1a"),
                description="csel w19, w8, wzr, ne in updateHardwareLevel",
            ),
            old_bytes=bytes.fromhex("13119f1a"),
            new_bytes=bytes.fromhex("13e19f1a"),
            fallback_offset=0xDBE44,
        ),
    ),
    plt_cave_va=0x10D394,
))
