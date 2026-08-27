import { useEffect, useMemo, useState } from "react";
import { checkBackendHealth } from "../api/shelfApi.js";
import { getHealthUrl } from "../config/api.js";

export default function useBackendStatus(apiUrl) {
  const [status, setStatus] = useState("checking");
  const healthUrl = useMemo(() => getHealthUrl(apiUrl), [apiUrl]);

  useEffect(() => {
    if (!healthUrl) {
      setStatus("invalid");
      return;
    }

    const controller = new AbortController();
    setStatus("checking");

    checkBackendHealth(healthUrl, controller.signal)
      .then((isHealthy) => setStatus(isHealthy ? "online" : "error"))
      .catch(() => setStatus("offline"));

    return () => controller.abort();
  }, [healthUrl]);

  return status;
}
