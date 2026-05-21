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
  } = useLiveGeneration(1500);

  const modelReady = health?.model_loaded ?? false;
  const offline = health?.status === "offline";

  const triggerLivePreview = useCallback(() => {
    if (!prompt.trim()) return;
    if (!canvasRef.current?.hasStrokes()) return;
    if (offline || !modelReady) return;

    scheduleGeneration(
      prompt,
      () => canvasRef.current?.exportSketch() ?? "",
      { controlnet_scale: sketchStrength, guidance_scale: 5.5 }
    );
  }, [prompt, sketchStrength, scheduleGeneration, offline, modelReady]);

  const handleClear = useCallback(() => {
    canvasRef.current?.clear();
    clearPreview();
  }, [clearPreview]);

  let hint: string | undefined;
  if (offline) {
    hint = "Start the Flask backend on port 5001, then draw to generate.";
  } else if (!modelReady) {
    hint = "Models are loading… you can type your prompt and sketch once ready.";
  } else if (!prompt.trim()) {
    hint = "Enter a description above, then draw.";
  }

  return (
    <div className="app">
      <div className="top-meta">
        <h1>Doodle Dust</h1>
        {offline ? (
          <p className="warn">Backend offline — start Flask on port 5001</p>
        ) : !modelReady ? (
          <p className="warn">Loading models… first run downloads ~4GB</p>
        ) : health?.device === "cpu" ? (
          <p className="warn">
            Running on CPU — very slow on MacBook Air. Restart backend after
            pulling latest code to use Apple GPU (mps) if available.
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
            onDrawingChange={triggerLivePreview}
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
