import { RefreshCw, Server } from "lucide-react";

const statusLabels = {
  online: "Backend connected",
  checking: "Checking backend",
  invalid: "Invalid API URL",
  error: "Backend offline",
  offline: "Backend offline",
};

export default function Sidebar({ apiUrl, backendStatus, onApiUrlChange, onReset }) {
  return (
    <aside className="sidebar">
      <div>
        <span className="eyebrow">Configuration</span>
        <h1>Smart Retail Shelf Monitoring</h1>
      </div>

      <label className="field-label" htmlFor="api-url">
        FastAPI URL
      </label>
      <input
        id="api-url"
        onChange={(event) => onApiUrlChange(event.target.value)}
        spellCheck="false"
        value={apiUrl}
      />

      <div className={`status-pill status-${backendStatus}`}>
        <Server size={16} />
        <span>{statusLabels[backendStatus] || "Backend offline"}</span>
      </div>

      <button className="secondary-button" onClick={onReset} type="button">
        <RefreshCw size={17} />
        Reset dashboard
      </button>
    </aside>
  );
}
