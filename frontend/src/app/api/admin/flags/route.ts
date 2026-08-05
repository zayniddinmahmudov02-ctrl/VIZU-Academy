import { mkdir, writeFile } from "fs/promises";
import path from "path";

import { NextRequest, NextResponse } from "next/server";

// The only Next.js route handler in this project — deliberate exception
// (see Phase "Language Management" design discussion): flag SVGs must live
// in frontend/public/flags/ so the browser can load them as plain static
// assets at /flags/{file}.svg, and only the Next.js process itself can
// write into its own public/ directory. There is no independent auth
// system here — every request is verified against the existing FastAPI
// backend's /users/me before anything is written to disk.

const ADMIN_PANEL_ROLES = new Set([
  "SUPER_ADMIN",
  "ADMIN",
  "CONTENT_MANAGER",
  "PAYMENT_MANAGER",
  "SUPPORT",
  "TEACHER",
]);

const MAX_SIZE_BYTES = 500 * 1024; // flags are tiny — 500KB is generous

async function requireAdmin(request: NextRequest): Promise<NextResponse | null> {
  const authHeader = request.headers.get("authorization");
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!authHeader || !apiUrl) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const meResponse = await fetch(`${apiUrl}/api/v1/users/me`, {
    headers: { Authorization: authHeader },
    cache: "no-store",
  });

  if (!meResponse.ok) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const me = (await meResponse.json()) as { role?: string };
  if (!me.role || !ADMIN_PANEL_ROLES.has(me.role)) {
    return NextResponse.json({ message: "Forbidden" }, { status: 403 });
  }

  return null;
}

export async function POST(request: NextRequest) {
  const authError = await requireAdmin(request);
  if (authError) return authError;

  const formData = await request.formData();
  const file = formData.get("file");
  const codeHint = formData.get("code");

  if (!(file instanceof File)) {
    return NextResponse.json({ message: "No file provided." }, { status: 400 });
  }

  if (file.size === 0 || file.size > MAX_SIZE_BYTES) {
    return NextResponse.json({ message: "File must be an SVG under 500KB." }, { status: 400 });
  }

  const looksLikeSvg = file.name.toLowerCase().endsWith(".svg") || file.type === "image/svg+xml";
  if (!looksLikeSvg) {
    return NextResponse.json({ message: "Only SVG files are allowed." }, { status: 400 });
  }

  const buffer = Buffer.from(await file.arrayBuffer());
  const head = buffer.subarray(0, 200).toString("utf-8").trimStart().toLowerCase();
  if (!head.startsWith("<?xml") && !head.startsWith("<svg")) {
    return NextResponse.json({ message: "File does not look like a valid SVG." }, { status: 400 });
  }

  const slugSource = typeof codeHint === "string" && codeHint.trim() ? codeHint : "flag";
  const slug = slugSource.toLowerCase().replace(/[^a-z0-9-]/g, "").slice(0, 20) || "flag";
  // A random suffix (not a fixed {code}.svg) avoids serving a stale,
  // browser-cached flag after an admin re-uploads a new one for the same
  // language — the DB's flag_file column just gets updated to match.
  const suffix = Math.random().toString(16).slice(2, 8);
  const filename = `${slug}-${suffix}.svg`;

  const flagsDir = path.join(process.cwd(), "public", "flags");
  await mkdir(flagsDir, { recursive: true });
  await writeFile(path.join(flagsDir, filename), buffer);

  return NextResponse.json({ filename }, { status: 201 });
}
