import { useCallback, useRef, useState } from "react";
import DrawingCanvas, {
  type DrawingCanvasHandle,
} from "./components/DrawingCanvas";
import PreviewPanel from "./components/PreviewPanel";
import PromptBar from "./components/PromptBar";
import { useLiveGeneration } from "./hooks/useLiveGeneration";

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [sketchStrength, setSketchStrength] = useState(1.0);
  const canvasRef = useRef<DrawingCanvasHandle>(null);

  const {
    preview,
    status,
    error,
    health,
    scheduleGeneration,
    clearPreview,
  } = useLiveGeneration(600);

  const modelReady = health?.model_loaded ?? false;
  const offline = health?.status === "offline";

  const triggerGeneration = useCallback(() => {
    if (!prompt.trim()) return;
    if (!canvasRef.current?.hasStrokes()) return;
    if (offline || !modelReady) return;

    scheduleGeneration(
      prompt,
      () => canvasRef.current?.exportSketch() ?? "",
      { controlnet_scale: sketchStrength, guidance_scale: 1.8 }
    );
  }, [prompt, sketchStrength, scheduleGeneration, offline, modelReady]);

  const handleClear = useCallback(() => {
    canvasRef.current?.clear();
    clearPreview();
  }, [clearPreview]);

  let hint: string | undefined;
  if (offline) {
    hint = "Start the Flask backend on port 5001.";
  } else if (!modelReady) {
    hint = "Loading Spooky AI models… first run downloads ~4GB.";
  } else if (!prompt.trim()) {
    hint = "Enter what you want to create, then draw.";
  } else {
    hint = "Preview updates shortly after you pause drawing.";
  }

  return (
    <div className="app">
      <div className="top-meta">
        <h1>Doodle Dust</h1>
        <p className="subtitle">Sketch on the left — Spooky AI preview on the right.</p>
        {offline ? (
          <p className="warn">Backend offline — start Flask on port 5001</p>
        ) : !modelReady ? (
          <p className="warn">Loading models… first run downloads ~4GB</p>
        ) : health?.device === "cpu" ? (
          <p className="warn">
            Running on CPU — very slow. Use an NVIDIA GPU (e.g. RTX 4060 Ti) for
            live previews.
          </p>
        ) : null}
      </div>

      <PromptBar
        prompt={prompt}
        onPromptChange={setPrompt}
        onClearCanvas={handleClear}
        sketchStrength={sketchStrength}
        onSketchStrengthChange={setSketchStrength}
        hint={hint}
      />

      <main className="workspace">
        <section className="pane pane-draw">
          <h2>Your sketch</h2>
          <DrawingCanvas
            ref={canvasRef}
            width={512}
            height={512}
            brushSize={5}
            onDrawingChange={triggerGeneration}
          />
        </section>
        <section className="pane pane-preview">
          <PreviewPanel
            image={preview}
            status={status}
            error={error}
            device={health?.device}
          />
        </section>
      </main>
    </div>
  );
}
