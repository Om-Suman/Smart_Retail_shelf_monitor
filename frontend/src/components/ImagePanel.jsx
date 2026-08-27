import { Boxes, ImageUp } from "lucide-react";

export default function ImagePanel({
  imageUrl,
  placeholder = "No image selected",
  title,
  type,
}) {
  const Icon = type === "result" ? Boxes : ImageUp;

  return (
    <article className="image-panel">
      <div className="panel-heading">
        <Icon size={18} />
        <h3>{title}</h3>
      </div>
      {imageUrl ? (
        <img alt={`${title} preview`} src={imageUrl} />
      ) : (
        <div className="empty-state">{placeholder}</div>
      )}
    </article>
  );
}
