export const DEFAULT_API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1/detect";

export function getHealthUrl(apiUrl) {
  try {
    const url = new URL(apiUrl);
    return `${url.origin}/health`;
  } catch {
    return "";
  }
}
