/** Opens a PDF / file blob in a new tab ("view"), or saves it under `filename`. */
export function openBlob(blob: Blob, filename?: string): void {
  const url = URL.createObjectURL(blob);
  if (filename) {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
    return;
  }
  // no "noopener": with it window.open always returns null (the fallback would always fire);
  // a same-origin blob: URL has no opener risk
  const win = window.open(url, "_blank");
  if (!win) {
    // pop-up blocked: fall back to a download
    openBlob(blob, "zertifikat.pdf");
  }
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
