import React, { useMemo, useRef, useState } from "react";
import { Activity, Boxes, Server } from "lucide-react";
import { detectShelfImage } from "./api/shelfApi.js";
import Sidebar from "./components/Sidebar.jsx";
import Topbar from "./components/Topbar.jsx";
import UploadPanel from "./components/UploadPanel.jsx";
import ImagePanel from "./components/ImagePanel.jsx";
import MetricCard from "./components/MetricCard.jsx";
import ResultsDashboard from "./components/ResultsDashboard.jsx";
import { DEFAULT_API_URL } from "./config/api.js";
import useBackendStatus from "./hooks/useBackendStatus.js";
import useObjectUrl from "./hooks/useObjectUrl.js";
import { formatMs } from "./utils/formatters.js";

export default function App() {
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isDetecting, setIsDetecting] = useState(false);
  const inputRef = useRef(null);

  const previewUrl = useObjectUrl(selectedFile);
  const backendStatus = useBackendStatus(apiUrl);
  const metadata = result?.metadata || {};

  const annotatedImageUrl = useMemo(() => {
    if (!result?.annotated_image) {
      return "";
    }

    return `data:image/jpeg;base64,${result.annotated_image}`;
  }, [result]);

  function handleFileChange(file) {
    setSelectedFile(file);
    setResult(null);
    setError("");
  }

  async function runDetection() {
    if (!selectedFile) {
      setError("Choose a shelf image before running detection.");
      return;
    }

    setIsDetecting(true);
    setError("");

    try {
      const payload = await detectShelfImage(apiUrl, selectedFile);
      setResult(payload);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setIsDetecting(false);
    }
  }

  function resetDashboard() {
    setSelectedFile(null);
    setResult(null);
    setError("");

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <main className="app-shell">
      <Sidebar
        apiUrl={apiUrl}
        backendStatus={backendStatus}
        onApiUrlChange={setApiUrl}
        onReset={resetDashboard}
      />

      <section className="workspace">
        <Topbar
          disabled={!selectedFile || isDetecting}
          isDetecting={isDetecting}
          onDetect={runDetection}
        />

        <UploadPanel
          error={error}
          inputRef={inputRef}
          onFileChange={handleFileChange}
          selectedFile={selectedFile}
        />

        <section className="image-grid">
          <ImagePanel
            imageUrl={previewUrl}
            title="Original Image"
            type="original"
          />
          <ImagePanel
            imageUrl={annotatedImageUrl}
            placeholder="Results will appear after detection"
            title="Detection Result"
            type="result"
          />
        </section>

        {result && (
          <>
            <section className="metrics-grid">
              <MetricCard
                icon={Boxes}
                label="Objects detected"
                value={result.inventory.total_objects}
              />
              <MetricCard
                icon={Activity}
                label="Inference time"
                value={formatMs(metadata.inference_time_ms)}
              />
              <MetricCard
                icon={Server}
                label="Model"
                value={
                  metadata.model_names
                    ? metadata.model_names.join(", ")
                    : "Unknown"
                }
              />
            </section>

            <ResultsDashboard result={result} />
          </>
        )}
      </section>
    </main>
  );
}
