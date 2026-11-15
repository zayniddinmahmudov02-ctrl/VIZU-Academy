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

/** Prints a PDF blob through a hidden iframe (no extra tab). If the browser cannot print inline, the PDF opens in a new tab. */
export function printBlob(blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const frame = document.createElement("iframe");
  frame.setAttribute("aria-hidden", "true");
  frame.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden";
  frame.onload = () => {
    try {
      frame.contentWindow?.focus();
      frame.contentWindow?.print();
    } catch {
      window.open(url, "_blank");
    }
  };
  frame.src = url;
  document.body.appendChild(frame);
  setTimeout(() => {
    frame.remove();
    URL.revokeObjectURL(url);
  }, 120_000);
}
