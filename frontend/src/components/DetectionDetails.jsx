import { Activity } from "lucide-react";
import { formatPercent } from "../utils/formatters.js";

export default function DetectionDetails({ detections }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <Activity size={18} />
        <h3>Detection Details</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Class</th>
              <th>Confidence</th>
              <th>Model Source</th>
              <th>X Min</th>
              <th>Y Min</th>
              <th>X Max</th>
              <th>Y Max</th>
            </tr>
          </thead>
          <tbody>
            {detections.map((detection, index) => (
              <tr
                key={`${detection.class_name}-${index}`}
                style={{
                  backgroundColor:
                    detection.model_source === "product"
                      ? "rgba(59, 130, 246, 0.05)"
                      : "rgba(168, 85, 247, 0.05)",
                }}
              >
                <td>{detection.class_name}</td>
                <td>{formatPercent(detection.confidence)}</td>
                <td>
                  <span
                    style={{
                      padding: "4px 8px",
                      borderRadius: "4px",
                      backgroundColor:
                        detection.model_source === "product"
                          ? "#3B82F6"
                          : "#A855F7",
                      color: "white",
                      fontSize: "0.85rem",
                      fontWeight: "bold",
                    }}
                  >
                    {detection.model_source === "product" ? "Product" : "Void"}
                  </span>
                </td>
                <td>{detection.x_min}</td>
                <td>{detection.y_min}</td>
                <td>{detection.x_max}</td>
                <td>{detection.y_max}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
