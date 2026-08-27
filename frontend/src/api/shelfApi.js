export async function detectShelfImage(apiUrl, file) {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(apiUrl, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(payload?.message || payload?.detail || response.statusText);
  }

  return payload;
}

export async function checkBackendHealth(healthUrl, signal) {
  const response = await fetch(healthUrl, { signal });
  return response.ok;
}
