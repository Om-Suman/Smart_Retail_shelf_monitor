export const DEFAULT_API_URL = import.meta.env.VITE_API_URL || "/api/v1/detect";

export function getHealthUrl(apiUrl) {
  try {
    const url = new URL(apiUrl);
    return `${url.origin}/health`;
  } catch {
    return "";
  }
}
