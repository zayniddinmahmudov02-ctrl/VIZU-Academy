"""Reads what an uploaded APK really is, without trusting the uploader's form fields.

* `inspect_apk(path)` → package, versionCode, versionName, minSdkVersion (from the binary AndroidManifest.xml),
  the SHA-256 of the file and of the signing certificate (APK Signature Scheme v2/v3 block, v1 JAR signature as
  fallback), and whether that certificate is the Android *debug* certificate.
* Pure stdlib + `cryptography` (already a dependency). Raises ApkError(code) for anything that is not a
  well-formed, signed APK; the service turns the code into an HTTP 400."""

import hashlib
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs7

APK_SIG_BLOCK_MAGIC = b"APK Sig Block 42"
V2_ID, V3_ID, V31_ID = 0x7109871A, 0xF05368C0, 0x1B93AD61
# android: attribute resource ids (stable across SDKs)
ATTR_VERSION_CODE, ATTR_VERSION_NAME, ATTR_MIN_SDK = 0x0101021B, 0x0101021C, 0x0101020C


class ApkError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ApkInfo:
    package: str
    version_code: int
    version_name: str
    min_sdk: int | None
    size_bytes: int
    sha256: str
    signer_sha256: str
    debug_signed: bool


# ── binary XML (AXML) ────────────────────────────────────────────────────────


def _string_pool(buf: bytes, off: int) -> list[str]:
    _type, header_size, _size, count, _styles, flags, strings_start, _styles_start = struct.unpack_from("<HHIIIIII", buf, off)
    utf8 = bool(flags & 0x100)
    offsets = struct.unpack_from(f"<{count}I", buf, off + header_size)
    base = off + strings_start
    out = []
    for o in offsets:
        p = base + o
        if utf8:
            n = buf[p]
            p += 2 if n & 0x80 else 1  # utf-16 length (skipped)
            n = buf[p]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | buf[p + 1]
                p += 2
            else:
                p += 1
            out.append(buf[p:p + n].decode("utf-8", "replace"))
        else:
            (n,) = struct.unpack_from("<H", buf, p)
            p += 2
            if n & 0x8000:
                (lo,) = struct.unpack_from("<H", buf, p)
                n = ((n & 0x7FFF) << 16) | lo
                p += 2
            out.append(buf[p:p + 2 * n].decode("utf-16-le", "replace"))
    return out


def parse_manifest(buf: bytes) -> dict:
    """package / versionCode / versionName / minSdkVersion from a compiled AndroidManifest.xml."""
    if len(buf) < 8 or struct.unpack_from("<H", buf, 0)[0] != 0x0003:
        raise ApkError("APK_INVALID_MANIFEST")
    strings: list[str] = []
    res_ids: list[int] = []
    result: dict = {}
    off = struct.unpack_from("<H", buf, 2)[0]
    while off + 8 <= len(buf):
        ctype, _hsize, csize = struct.unpack_from("<HHI", buf, off)
        if csize < 8:
            break
        if ctype == 0x0001:
            strings = _string_pool(buf, off)
        elif ctype == 0x0180:
            res_ids = list(struct.unpack_from(f"<{(csize - 8) // 4}I", buf, off + 8))
        elif ctype == 0x0102:  # start element
            _ns, name_i, attr_start, attr_size, attr_count = struct.unpack_from("<IIHHH", buf, off + 16)
            tag = strings[name_i] if name_i < len(strings) else ""
            for a in range(attr_count):
                ap = off + 16 + attr_start + a * attr_size
                _ans, aname, raw, _vsize, _res0, dtype, data = struct.unpack_from("<IIIHBBI", buf, ap)
                rid = res_ids[aname] if aname < len(res_ids) else None
                label = strings[aname] if aname < len(strings) else ""
                value = strings[raw] if raw != 0xFFFFFFFF and raw < len(strings) else (data if dtype in (0x10, 0x11) else None)
                if tag == "manifest" and label == "package":
                    result["package"] = value
                elif tag == "manifest" and (rid == ATTR_VERSION_CODE or label == "versionCode"):
                    result["version_code"] = int(value) if value is not None else None
                elif tag == "manifest" and (rid == ATTR_VERSION_NAME or label == "versionName"):
                    result["version_name"] = str(value) if value is not None else None
                elif tag == "uses-sdk" and (rid == ATTR_MIN_SDK or label == "minSdkVersion"):
                    result["min_sdk"] = int(value) if value is not None and str(value).isdigit() else None
        off += csize
    if not result.get("package") or result.get("version_code") is None or not result.get("version_name"):
        raise ApkError("APK_INVALID_MANIFEST")
    return result


# ── signatures ───────────────────────────────────────────────────────────────


def _lp(buf: bytes, p: int) -> tuple[bytes, int]:
    (n,) = struct.unpack_from("<I", buf, p)
    return buf[p + 4:p + 4 + n], p + 4 + n


def _v2_certificate(path: Path) -> bytes | None:
    """DER of the first signer's certificate from the APK Signing Block (v3 > v2), or None if there is none."""
    data = path.read_bytes()
    eocd = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if eocd < 0:
        return None
    (cd_offset,) = struct.unpack_from("<I", data, eocd + 16)
    if cd_offset < 32 or data[cd_offset - 16:cd_offset] != APK_SIG_BLOCK_MAGIC:
        return None
    (block_size,) = struct.unpack_from("<Q", data, cd_offset - 24)
    start = cd_offset - block_size - 8
    if start < 0:
        return None
    pairs: dict[int, bytes] = {}
    p, end = start + 8, cd_offset - 24
    while p + 12 <= end:
        (n,) = struct.unpack_from("<Q", data, p)
        (pid,) = struct.unpack_from("<I", data, p + 8)
        pairs[pid] = data[p + 12:p + 8 + n]
        p += 8 + n
    for pid in (V31_ID, V3_ID, V2_ID):
        if pid not in pairs:
            continue
        signers, _ = _lp(pairs[pid], 0)
        signer, _ = _lp(signers, 0)
        signed_data, _ = _lp(signer, 0)
        _digests, q = _lp(signed_data, 0)
        certs, _ = _lp(signed_data, q)
        cert, _ = _lp(certs, 0)
        return cert or None
    return None


def _v1_certificate(zf: zipfile.ZipFile) -> bytes | None:
    for name in zf.namelist():
        upper = name.upper()
        if upper.startswith("META-INF/") and upper.endswith((".RSA", ".DSA", ".EC")):
            certs = pkcs7.load_der_pkcs7_certificates(zf.read(name))
            if certs:
                from cryptography.hazmat.primitives.serialization import Encoding

                return certs[0].public_bytes(Encoding.DER)
    return None


def inspect_apk(path: Path) -> ApkInfo:
    if not zipfile.is_zipfile(path):
        raise ApkError("APK_INVALID")
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if "AndroidManifest.xml" not in names or not any(n.startswith("classes") and n.endswith(".dex") for n in names):
            raise ApkError("APK_INVALID")
        manifest = parse_manifest(zf.read("AndroidManifest.xml"))
        try:
            der = _v2_certificate(path) or _v1_certificate(zf)
        except (struct.error, ValueError):
            der = None
    if not der:
        raise ApkError("APK_NOT_SIGNED")
    cert = x509.load_der_x509_certificate(der)
    subject = cert.subject.rfc4514_string()
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(chunk)
    return ApkInfo(
        package=manifest["package"],
        version_code=manifest["version_code"],
        version_name=manifest["version_name"],
        min_sdk=manifest.get("min_sdk"),
        size_bytes=path.stat().st_size,
        sha256=sha.hexdigest(),
        signer_sha256=cert.fingerprint(hashes.SHA256()).hex(),
        debug_signed="CN=Android Debug" in subject,
    )


# Android API level → marketing version, for the download page ("Android 7.0 oder neuer").
ANDROID_VERSIONS = {21: "5.0", 22: "5.1", 23: "6.0", 24: "7.0", 25: "7.1", 26: "8.0", 27: "8.1", 28: "9", 29: "10",
                    30: "11", 31: "12", 32: "12L", 33: "13", 34: "14", 35: "15", 36: "16"}
