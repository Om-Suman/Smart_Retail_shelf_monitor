export default function MetricCard({ label, value, icon: Icon }) {
  return (
    <section className="metric-card">
      <div className="metric-icon">
        <Icon size={20} />
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </section>
  );
}
