import type { CSSProperties } from "react";

interface Props {
  mode: "waiting" | "generating";
}

export default function GeneratingOverlay({ mode }: Props) {
  const isGenerating = mode === "generating";

  return (
    <div
      className={`gen-overlay ${isGenerating ? "gen-overlay--active" : "gen-overlay--waiting"}`}
      role="status"
      aria-live="polite"
    >
      <div className="gen-aurora" aria-hidden="true" />
      <div className="gen-aurora gen-aurora--2" aria-hidden="true" />
      <div className="gen-scanlines" aria-hidden="true" />
      <div className="gen-grid" aria-hidden="true" />

      <div className="gen-particles" aria-hidden="true">
        {Array.from({ length: 18 }).map((_, i) => (
          <span
            key={i}
            className="gen-particle"
            style={{ "--i": i } as CSSProperties}
          />
        ))}
      </div>

      <div className="gen-content">
        <div className="gen-orbit">
          <span className="gen-orbit-dot" />
          <span className="gen-orbit-dot gen-orbit-dot--2" />
          <span className="gen-orbit-dot gen-orbit-dot--3" />
        </div>

        <p className="gen-title">
          {isGenerating ? "Spooky AI" : "Doodle Dust"}
        </p>
        <p className="gen-sub">
          {isGenerating
            ? "Summoning your image from the void…"
            : "Hold still a moment…"}
        </p>

        <div className="gen-bar">
          <span className="gen-bar-fill" />
        </div>

        <div className="gen-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
