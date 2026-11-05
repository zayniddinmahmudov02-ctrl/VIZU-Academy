"""Profile photo upload: content checks (signature vs declared type, size, dimensions), crop box maths, EXIF
orientation, re-encoding to a 512×512 WebP, and the /users/me/photo endpoint storing only the processed file
under a random name (storage + DB calls mocked)."""

import asyncio
import io
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException


def _img(size=(800, 600), fmt="PNG", color=(10, 120, 200), exif_rotate=False) -> bytes:
    from PIL import Image

    img = Image.new("RGB", size, color)
    img.paste((250, 10, 10), (0, 0, size[0] // 4, size[1] // 4))  # red marker top-left
    out = io.BytesIO()
    if exif_rotate:
        exif = img.getexif()
        exif[0x0112] = 6  # rotate 90° clockwise when displayed
        img.save(out, fmt, exif=exif)
    else:
        img.save(out, fmt)
    return out.getvalue()


class TestCropBox(unittest.TestCase):
    def test_centre_square_by_default(self):
        from app.services.profile_photo import crop_box

        self.assertEqual(crop_box(800, 600, None, None, None), (100, 0, 700, 600))
        self.assertEqual(crop_box(600, 800, None, None, None), (0, 100, 600, 700))

    def test_fractions_and_clamping(self):
        from app.services.profile_photo import crop_box

        self.assertEqual(crop_box(800, 600, 0.0, 0.0, 0.5), (0, 0, 300, 300))
        self.assertEqual(crop_box(800, 600, 0.9, 0.9, 0.5), (500, 300, 800, 600))  # pushed back inside
        self.assertEqual(crop_box(800, 600, 0.0, 0.0, 0.001)[2], 30)  # minimum 5 % of the short side


class TestProcess(unittest.TestCase):
    def test_output_is_square_webp_without_metadata(self):
        from PIL import Image

        from app.services.profile_photo import OUTPUT, process

        out = process(_img(fmt="JPEG"), "me.jpg", "image/jpeg")
        img = Image.open(io.BytesIO(out))
        self.assertEqual((img.format, img.size), ("WEBP", (OUTPUT, OUTPUT)))
        self.assertFalse(img.getexif())

    def test_crop_keeps_the_chosen_corner(self):
        from PIL import Image

        from app.services.profile_photo import process

        out = Image.open(io.BytesIO(process(_img(), "a.png", "image/png", 0.0, 0.0, 0.25))).convert("RGB")
        r, g, b = out.getpixel((256, 256))
        self.assertGreater(r, 200)
        self.assertLess(b, 80)

    def test_exif_orientation_is_applied(self):
        from PIL import Image

        from app.services.profile_photo import process

        # 800×600 landscape with orientation 6 is displayed as 600×800 portrait: the red marker ends up top-right
        out = Image.open(io.BytesIO(process(_img(fmt="JPEG", exif_rotate=True), "a.jpg", "image/jpeg", 0.0, 0.0, 1.0))).convert("RGB")
        self.assertGreater(out.getpixel((500, 10))[0], 200)
        self.assertLess(out.getpixel((10, 10))[0], 100)

    def test_rejections(self):
        from app.services.profile_photo import MAX_BYTES, process

        cases = [
            (b"", "a.png", "image/png", "PHOTO_EMPTY"),
            (b"<svg onload=alert(1)>", "a.png", "image/png", "PHOTO_INVALID"),
            (b"GIF89a" + b"\0" * 100, "a.png", "image/png", "PHOTO_INVALID"),
            (_img(fmt="PNG"), "a.jpg", "image/jpeg", "PHOTO_TYPE_MISMATCH"),
            (_img(fmt="GIF"), "a.png", "image/png", "PHOTO_TYPE_MISMATCH"),
            (_img(size=(80, 80)), "a.png", "image/png", "PHOTO_TOO_SMALL"),
            (_img(), "a.svg", "image/png", "PHOTO_EXTENSION"),
            (b"x" * (MAX_BYTES + 1), "a.png", "image/png", None),
        ]
        for data, name, mime, code in cases:
            with self.subTest(code=code), self.assertRaises(HTTPException) as ctx:
                process(data, name, mime)
            self.assertEqual(ctx.exception.status_code, 400)
            if code:
                self.assertEqual(ctx.exception.detail, code)


class TestEndpoint(unittest.TestCase):
    def _file(self, data, name="me.png", mime="image/png"):
        from fastapi import UploadFile
        from starlette.datastructures import Headers

        return UploadFile(file=io.BytesIO(data), filename=name, headers=Headers({"content-type": mime}))

    def test_stores_processed_webp_under_random_name_and_replaces_old(self):
        from app.api.users import router as users_router

        user = SimpleNamespace(profile_image="/uploads/avatars/old.jpg")
        stored = {}

        async def fake_upload(self, file, folder):
            stored["name"], stored["folder"], stored["data"] = file.filename, folder, await file.read()
            return {"url": f"/uploads/{folder}/{file.filename}"}

        with patch.object(users_router.UploadService, "upload", fake_upload), \
                patch.object(users_router.UploadService, "delete", AsyncMock()) as delete, \
                patch.object(users_router, "set_profile_image", lambda db, u, url: SimpleNamespace(profile_image=url)):
            result = asyncio.run(users_router.upload_my_photo(self._file(_img(), "../../evil.png"), 0.1, 0.0, 0.5, user, None))
        self.assertEqual(stored["folder"], "avatars")
        self.assertRegex(stored["name"], r"^[0-9a-f]{32}\.webp$")
        self.assertEqual(stored["data"][8:12], b"WEBP")
        self.assertEqual(result.profile_image, f"/uploads/avatars/{stored['name']}")
        delete.assert_awaited_once_with("avatars/old.jpg")

    def test_rejects_wrong_type_before_storing(self):
        from app.api.users import router as users_router

        with patch.object(users_router.UploadService, "upload", AsyncMock()) as upload:
            for data, mime in ((b"%PDF-1.4", "application/pdf"), (b"<svg/>", "image/png")):
                with self.subTest(mime=mime), self.assertRaises(HTTPException):
                    asyncio.run(users_router.upload_my_photo(self._file(data, "x.png", mime), None, None, None, SimpleNamespace(profile_image=None), None))
        upload.assert_not_called()

    def test_crop_fields_are_validated(self):
        from app.main import app

        schema = app.openapi()["components"]["schemas"]
        body = next(v for k, v in schema.items() if k.startswith("Body_upload_my_photo"))
        self.assertEqual(body["properties"]["crop_size"]["anyOf"][0].get("exclusiveMinimum"), 0.0)
        self.assertEqual(body["properties"]["crop_x"]["anyOf"][0].get("maximum"), 1.0)


if __name__ == "__main__":
    unittest.main()
