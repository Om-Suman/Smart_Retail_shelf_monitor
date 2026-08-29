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

    setStatus("checking");

    const checkHealth = async () => {
      try {
        const isHealthy = await checkBackendHealth(healthUrl);
        setStatus(isHealthy ? "online" : "error");
      } catch (error) {
        setStatus("offline");
      }
    };

    // Initial check after a small delay to allow server to start
    const timer = setTimeout(checkHealth, 500);

    // Retry every 5 seconds
    const intervalId = setInterval(checkHealth, 5000);

    return () => {
      clearTimeout(timer);
      clearInterval(intervalId);
    };
  }, [healthUrl]);

  return status;
}
