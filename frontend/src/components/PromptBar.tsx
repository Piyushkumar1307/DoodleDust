interface Props {
  prompt: string;
  onPromptChange: (value: string) => void;
  onClearCanvas: () => void;
  sketchStrength: number;
  onSketchStrengthChange: (value: number) => void;
  hint?: string;
}

export default function PromptBar({
  prompt,
  onPromptChange,
  onClearCanvas,
  sketchStrength,
  onSketchStrengthChange,
  hint,
}: Props) {
  return (
    <header className="prompt-bar">
      <label className="prompt-label" htmlFor="intent-prompt">
        Style & subject (sketch controls layout — draw rivers, paths, shapes)
      </label>
      <input
        id="intent-prompt"
        type="text"
        placeholder="e.g. sunset mountains with a river in the valley"
        value={prompt}
        onChange={(e) => onPromptChange(e.target.value)}
      />
      <div className="prompt-actions">
        <button type="button" className="secondary" onClick={onClearCanvas}>
          Clear canvas
        </button>
      </div>

      <div className="sketch-strength">
        <label htmlFor="sketch-strength">
          Follow sketch: <strong>{sketchStrength.toFixed(2)}</strong>
        </label>
        <input
          id="sketch-strength"
          type="range"
          min={0.6}
          max={1.2}
          step={0.05}
          value={sketchStrength}
          onChange={(e) => onSketchStrengthChange(parseFloat(e.target.value))}
        />
        <span className="range-hint">Higher = match your drawing more closely</span>
      </div>

      {hint ? <p className="prompt-hint">{hint}</p> : null}
    </header>
  );
}
