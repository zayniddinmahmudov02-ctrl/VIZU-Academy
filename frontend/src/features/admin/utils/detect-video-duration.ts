/** Reads a video file's duration client-side (via a throwaway <video>
 *  element) so the admin never has to type it in by hand — there's no
 *  server-side media-inspection dependency installed. */
export function detectVideoDuration(file: File): Promise<number> {
  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file);
    const probe = document.createElement("video");

    probe.preload = "metadata";
    probe.onloadedmetadata = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(Number.isFinite(probe.duration) ? Math.round(probe.duration) : 0);
    };
    probe.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(0);
    };
    probe.src = objectUrl;
  });
}
