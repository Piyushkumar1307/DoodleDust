import GeneratingOverlay from "./GeneratingOverlay";
import "./GeneratingOverlay.css";

interface Props {
  image: string | null;
  status: "idle" | "waiting" | "generating" | "error" | "live";
  error: string | null;
  device?: string;
}

export default function PreviewPanel({ image, status, error, device }: Props) {
  const busy = status === "waiting" || status === "generating";
  const overlayMode = status === "generating" ? "generating" : "waiting";

  return (
    <div className="preview-panel">
      <div className="preview-header">
        <span>Spooky AI preview</span>
        {device && <span className="badge">{device}</span>}
      </div>
      <div className={`preview-frame ${busy ? "is-busy" : ""}`}>
        {image ? (
          <img src={image} alt="Generated preview" />
        ) : (
          <div className="preview-placeholder">
            Enter a prompt and draw — Spooky AI develops here
          </div>
        )}
        {busy && <GeneratingOverlay mode={overlayMode} />}
      </div>
      {error && <p className="preview-error">{error}</p>}
    </div>
  );
}
