import { UploadCloud } from "lucide-react";

export default function UploadPanel({
  error,
  inputRef,
  onFileChange,
  selectedFile,
}) {
  function handleChange(event) {
    const file = event.target.files?.[0];

    if (file) {
      onFileChange(file);
    }
  }

  return (
    <section className="upload-panel">
      <input
        accept=".jpg,.jpeg,.png,image/jpeg,image/png,image"
        className="file-input"
        id="shelf-image"
        onChange={handleChange}
        ref={inputRef}
        type="file"
      />
      <label className="dropzone" htmlFor="shelf-image">
        <UploadCloud size={28} />
        <span>{selectedFile ? selectedFile.name : "Upload shelf image"}</span>
        <small>JPG, JPEG, PNG</small>
      </label>
      {error && <p className="error-message">{error}</p>}
    </section>
  );
}
