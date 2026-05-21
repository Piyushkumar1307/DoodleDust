import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

export interface DrawingCanvasHandle {
  exportSketch: () => string;
  clear: () => void;
  hasStrokes: () => boolean;
}

interface Props {
  width?: number;
  height?: number;
  brushSize?: number;
  /** Fired when user puts ink on canvas (start/move/end of a stroke). */
  onDrawingChange?: () => void;
}

const DrawingCanvas = forwardRef<DrawingCanvasHandle, Props>(
  function DrawingCanvas(
    { width = 512, height = 512, brushSize = 4, onDrawingChange },
    ref
  ) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const drawing = useRef(false);
    const last = useRef<{ x: number; y: number } | null>(null);
    const hasInk = useRef(false);

    const getCtx = () => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      return canvas.getContext("2d");
    };

    const fillBackground = useCallback(() => {
      const ctx = getCtx();
      if (!ctx) return;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);
    }, [width, height]);

    useEffect(() => {
      fillBackground();
    }, [fillBackground]);

    const notifyDrawing = useCallback(() => {
      onDrawingChange?.();
    }, [onDrawingChange]);

    useImperativeHandle(ref, () => ({
      exportSketch: () => {
        const canvas = canvasRef.current;
        if (!canvas) return "";
        return canvas.toDataURL("image/png");
      },
      hasStrokes: () => hasInk.current,
      clear: () => {
        fillBackground();
        hasInk.current = false;
      },
    }));

    const pointerPos = (e: React.PointerEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current!;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    };

    const stampInk = (x: number, y: number) => {
      const ctx = getCtx();
      if (!ctx) return;
      ctx.fillStyle = "#000000";
      ctx.beginPath();
      ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
      ctx.fill();
      hasInk.current = true;
    };

    const drawLine = (x: number, y: number) => {
      const ctx = getCtx();
      if (!ctx || !last.current) return;
      ctx.strokeStyle = "#000000";
      ctx.lineWidth = brushSize;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.beginPath();
      ctx.moveTo(last.current.x, last.current.y);
      ctx.lineTo(x, y);
      ctx.stroke();
      last.current = { x, y };
      hasInk.current = true;
    };

    const onDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
      e.currentTarget.setPointerCapture(e.pointerId);
      drawing.current = true;
      const pos = pointerPos(e);
      last.current = pos;
      stampInk(pos.x, pos.y);
      notifyDrawing();
    };

    const onMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!drawing.current) return;
      const pos = pointerPos(e);
      drawLine(pos.x, pos.y);
      notifyDrawing();
    };

    const onUp = () => {
      if (!drawing.current) return;
      drawing.current = false;
      last.current = null;
      if (hasInk.current) notifyDrawing();
    };

    return (
      <canvas
        ref={canvasRef}
        className="drawing-canvas"
        width={width}
        height={height}
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={onUp}
        onPointerLeave={onUp}
      />
    );
  }
);

export default DrawingCanvas;
