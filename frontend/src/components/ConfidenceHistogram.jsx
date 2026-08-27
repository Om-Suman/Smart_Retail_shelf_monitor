export default function ConfidenceHistogram({ detections }) {
  const bins = Array.from({ length: 10 }, (_, index) => ({
    label: `${index * 10}-${(index + 1) * 10}%`,
    count: 0,
  }));

  detections.forEach((detection) => {
    const index = Math.min(Math.floor(Number(detection.confidence) * 10), 9);
    bins[index].count += 1;
  });

  const maxCount = Math.max(...bins.map((bin) => bin.count), 1);

  return (
    <div className="histogram" aria-label="Confidence distribution">
      {bins.map((bin) => (
        <div className="histogram-bin" key={bin.label}>
          <div
            className="histogram-bar"
            style={{ height: `${Math.max((bin.count / maxCount) * 100, 4)}%` }}
            title={`${bin.label}: ${bin.count}`}
          />
          <span>{bin.label}</span>
        </div>
      ))}
    </div>
  );
}
