import GeneratingOverlay from "./GeneratingOverlay";
import "./GeneratingOverlay.css";

interface Props {
  image: string | null;
  status: "idle" | "waiting" | "generating" | "error";
  error: string | null;
  device?: string;
}

export default function PreviewPanel({ image, status, error, device }: Props) {
  const busy = status === "waiting" || status === "generating";
  const overlayMode = status === "generating" ? "generating" : "waiting";

  return (
    <div className="preview-panel">
      <div className="preview-header">
        <span>AI preview</span>
        {device && <span className="badge">{device}</span>}
      </div>
      <div className={`preview-frame ${busy ? "is-busy" : ""}`}>
        {image ? (
          <img src={image} alt="Generated preview" />
        ) : (
          <div className="preview-placeholder">
            Draw on the left — preview appears here
          </div>
        )}
        {busy && <GeneratingOverlay mode={overlayMode} />}
      </div>
      {error && <p className="preview-error">{error}</p>}
    </div>
  );
}
