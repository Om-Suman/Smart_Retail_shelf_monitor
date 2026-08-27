import { Activity, Loader2 } from "lucide-react";

export default function Topbar({ disabled, isDetecting, onDetect }) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">Computer Vision Inventory</span>
        <h2>Upload a shelf image and review detections in one place.</h2>
      </div>

      <button className="primary-button" disabled={disabled} onClick={onDetect} type="button">
        {isDetecting ? <Loader2 className="spin" size={18} /> : <Activity size={18} />}
        {isDetecting ? "Running inference" : "Detect products"}
      </button>
    </header>
  );
}
