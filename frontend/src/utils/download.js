export function downloadBase64Image(base64Value, fileName) {
  const link = document.createElement("a");
  link.href = `data:image/jpeg;base64,${base64Value}`;
  link.download = fileName;
  link.click();
}
