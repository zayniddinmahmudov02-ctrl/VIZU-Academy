import importlib
import pathlib
import traceback
import sys

ROOT = pathlib.Path("app")
OUTPUT = pathlib.Path("import_errors.txt")

errors = []

with OUTPUT.open("w", encoding="utf-8") as report:

    report.write("=" * 100 + "\n")
    report.write("VIZU Academy Backend Import Report\n")
    report.write("=" * 100 + "\n\n")

    for file in sorted(ROOT.rglob("*.py")):

        if "__pycache__" in file.parts:
            continue

        module = ".".join(file.with_suffix("").parts)

        try:
            importlib.import_module(module)

        except Exception:

            tb = traceback.format_exc()

            errors.append(module)

            report.write(f"[ERROR] {module}\n")
            report.write("-" * 100 + "\n")
            report.write(tb)
            report.write("\n\n")

    report.write("=" * 100 + "\n")
    report.write(f"TOTAL ERRORS: {len(errors)}\n")
    report.write("=" * 100 + "\n")

print(f"\nImport tekshiruvi tugadi.")
print(f"Xatolar: {len(errors)}")
print(f"Hisobot saqlandi: {OUTPUT.resolve()}")

sys.exit(1 if errors else 0)