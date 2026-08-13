/** Byte/speed/time formatting shared by every upload-progress UI. Kept in
 * one place so "1.50 GB" / "8.4 MB/s" / "~1 min 12 sec" render identically
 * everywhere a file upload is shown, instead of each component rolling
 * its own rounding rules. */

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  if (bytes < 1024 ** 2) return `${Math.round(bytes / 1024)} KB`;

  if (bytes < 1024 ** 3) {
    const mb = Math.round((bytes / 1024 ** 2) * 10) / 10;
    return `${mb % 1 === 0 ? mb.toFixed(0) : mb.toFixed(1)} MB`;
  }

  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export function formatUploadSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond < 1024 ** 2) {
    return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
  }
  return `${(bytesPerSecond / 1024 ** 2).toFixed(1)} MB/s`;
}

export function formatRemainingTime(seconds: number): string {
  if (seconds < 1) return "~1 sec";
  if (seconds < 60) return `~${Math.round(seconds)} sec`;

  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);

  return secs === 0 ? `~${minutes} min` : `~${minutes} min ${secs} sec`;
}
