import { Activity, BarChart3, Download } from "lucide-react";
import ConfidenceHistogram from "./ConfidenceHistogram.jsx";
import DetectionDetails from "./DetectionDetails.jsx";
import InventoryBars from "./InventoryBars.jsx";
import InventorySummary from "./InventorySummary.jsx";
import MetricCard from "./MetricCard.jsx";
import { downloadBase64Image } from "../utils/download.js";
import { formatMs, formatPercent } from "../utils/formatters.js";

export default function ResultsDashboard({ result }) {
  const products = result.inventory?.products || [];
  const detections = result.detections || [];
  const metadata = result.metadata || {};
  const confidences = detections.map((detection) => Number(detection.confidence));
  const averageConfidence =
    confidences.length > 0
      ? confidences.reduce((sum, value) => sum + value, 0) / confidences.length
      : 0;
  const highestConfidence = confidences.length > 0 ? Math.max(...confidences) : 0;
  const lowestConfidence = confidences.length > 0 ? Math.min(...confidences) : 0;

  return (
    <>
      <section className="analytics-grid">
        <InventorySummary products={products} />

        <article className="panel">
          <div className="panel-heading">
            <BarChart3 size={18} />
            <h3>Inventory Distribution</h3>
          </div>
          <InventoryBars products={products} />
        </article>
      </section>

      <DetectionDetails detections={detections} />

      <section className="analytics-grid">
        <article className="panel">
          <div className="panel-heading">
            <Activity size={18} />
            <h3>Confidence Statistics</h3>
          </div>
          <div className="compact-metrics">
            <MetricCard icon={Activity} label="Average" value={formatPercent(averageConfidence)} />
            <MetricCard icon={Activity} label="Highest" value={formatPercent(highestConfidence)} />
            <MetricCard icon={Activity} label="Lowest" value={formatPercent(lowestConfidence)} />
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <BarChart3 size={18} />
            <h3>Confidence Distribution</h3>
          </div>
          <ConfidenceHistogram detections={detections} />
        </article>
      </section>

      <section className="summary-strip">
        <div>
          <span className="eyebrow">Session Summary</span>
          <p>
            {result.inventory.total_objects} objects detected with{" "}
            {metadata.model_name || "the selected model"} in {formatMs(metadata.inference_time_ms)}{" "}
            from a {metadata.image_width} x {metadata.image_height} image.
          </p>
        </div>
        <button
          className="secondary-button"
          onClick={() => downloadBase64Image(result.annotated_image, "annotated_detection.jpg")}
          type="button"
        >
          <Download size={17} />
          Download annotated image
        </button>
      </section>
    </>
  );
}
