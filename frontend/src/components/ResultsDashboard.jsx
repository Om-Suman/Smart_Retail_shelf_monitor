import { Activity, BarChart3, Download, Package, Inbox } from "lucide-react";
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

  // Count detections by model source
  const productDetections = detections.filter(
    (d) => d.model_source === "product",
  ).length;
  const voidDetections = detections.filter(
    (d) => d.model_source === "void",
  ).length;

  const confidences = detections.map((detection) =>
    Number(detection.confidence),
  );
  const averageConfidence =
    confidences.length > 0
      ? confidences.reduce((sum, value) => sum + value, 0) / confidences.length
      : 0;
  const highestConfidence =
    confidences.length > 0 ? Math.max(...confidences) : 0;
  const lowestConfidence =
    confidences.length > 0 ? Math.min(...confidences) : 0;

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
            <MetricCard
              icon={Activity}
              label="Average"
              value={formatPercent(averageConfidence)}
            />
            <MetricCard
              icon={Activity}
              label="Highest"
              value={formatPercent(highestConfidence)}
            />
            <MetricCard
              icon={Activity}
              label="Lowest"
              value={formatPercent(lowestConfidence)}
            />
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

      <section className="analytics-grid">
        <article
          className="panel"
          style={{
            backgroundColor: "rgba(59, 130, 246, 0.05)",
            borderLeft: "4px solid #3B82F6",
          }}
        >
          <div className="panel-heading">
            <Package size={20} style={{ color: "#3B82F6" }} />
            <h3 style={{ color: "#1F2937" }}>Product Detections</h3>
          </div>
          <div
            style={{
              padding: "16px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: "bold",
                color: "#3B82F6",
                marginBottom: "8px",
              }}
            >
              {productDetections}
            </div>
            <div
              style={{
                fontSize: "0.95rem",
                color: "#666",
                marginBottom: "12px",
              }}
            >
              Products detected
            </div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: "600",
                color: "#1F2937",
              }}
            >
              Inference Time:{" "}
              <span style={{ color: "#3B82F6" }}>
                {formatMs(metadata.model_times_ms?.product_best || 0)}
              </span>
            </div>
          </div>
        </article>

        <article
          className="panel"
          style={{
            backgroundColor: "rgba(168, 85, 247, 0.05)",
            borderLeft: "4px solid #A855F7",
          }}
        >
          <div className="panel-heading">
            <Inbox size={20} style={{ color: "#A855F7" }} />
            <h3 style={{ color: "#1F2937" }}>Void Detections</h3>
          </div>
          <div
            style={{
              padding: "16px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: "bold",
                color: "#A855F7",
                marginBottom: "8px",
              }}
            >
              {voidDetections}
            </div>
            <div
              style={{
                fontSize: "0.95rem",
                color: "#666",
                marginBottom: "12px",
              }}
            >
              Voids detected
            </div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: "600",
                color: "#1F2937",
              }}
            >
              Inference Time:{" "}
              <span style={{ color: "#A855F7" }}>
                {formatMs(metadata.model_times_ms?.void_best || 0)}
              </span>
            </div>
          </div>
        </article>
      </section>

      <section className="summary-strip">
        <div>
          <span className="eyebrow">Detection Summary</span>
          <div
            style={{
              display: "flex",
              gap: "24px",
              marginTop: "12px",
            }}
          >
            <div>
              <span style={{ fontSize: "0.9rem", color: "#666" }}>
                Total Detected:
              </span>
              <p
                style={{
                  fontSize: "1.3rem",
                  fontWeight: "bold",
                  color: "#1F2937",
                  margin: "4px 0 0 0",
                }}
              >
                {productDetections + voidDetections}
              </p>
            </div>
            <div>
              <span style={{ fontSize: "0.9rem", color: "#666" }}>
                Product Ratio:
              </span>
              <p
                style={{
                  fontSize: "1.3rem",
                  fontWeight: "bold",
                  color: "#3B82F6",
                  margin: "4px 0 0 0",
                }}
              >
                {productDetections + voidDetections > 0
                  ? (
                      (productDetections /
                        (productDetections + voidDetections)) *
                      100
                    ).toFixed(1)
                  : 0}
                %
              </p>
            </div>
            <div>
              <span style={{ fontSize: "0.9rem", color: "#666" }}>
                Void Ratio:
              </span>
              <p
                style={{
                  fontSize: "1.3rem",
                  fontWeight: "bold",
                  color: "#A855F7",
                  margin: "4px 0 0 0",
                }}
              >
                {productDetections + voidDetections > 0
                  ? (
                      (voidDetections / (productDetections + voidDetections)) *
                      100
                    ).toFixed(1)
                  : 0}
                %
              </p>
            </div>
          </div>
        </div>
        <button
          className="secondary-button"
          onClick={() =>
            downloadBase64Image(
              result.annotated_image,
              "annotated_detection.jpg",
            )
          }
          type="button"
        >
          <Download size={17} />
          Download annotated image
        </button>
      </section>
    </>
  );
}
