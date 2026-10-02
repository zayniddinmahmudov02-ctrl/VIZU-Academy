"use client";

import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

/** Live microphone level as mirrored bars (VIZU blue -> orange). Drawn on a
 * canvas from the AnalyserNode — no React re-render per frame. With reduced
 * motion a calm, static bar row is shown instead. */
export default function SprechenWaveform({ analyser, active }: { analyser: AnalyserNode | null; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const width = (canvas.width = canvas.clientWidth * window.devicePixelRatio);
    const height = (canvas.height = canvas.clientHeight * window.devicePixelRatio);
    const bars = 40;
    const gap = width / bars;
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, "#2563eb");
    gradient.addColorStop(1, "#f97316");

    const draw = (levels: number[]) => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = gradient;
      levels.forEach((level, i) => {
        const h = Math.max(height * 0.06, level * height * 0.9);
        const x = i * gap + gap * 0.2;
        ctx.beginPath();
        ctx.roundRect(x, (height - h) / 2, gap * 0.6, h, gap * 0.3);
        ctx.fill();
      });
    };

    if (!active || !analyser || reduce) {
      draw(Array.from({ length: bars }, (_, i) => (active ? 0.25 + 0.1 * Math.sin(i) : 0.08)));
      return;
    }
    const data = new Uint8Array(analyser.frequencyBinCount);
    let frame = 0;
    const loop = () => {
      analyser.getByteFrequencyData(data);
      const step = Math.floor(data.length / bars) || 1;
      draw(Array.from({ length: bars }, (_, i) => data[i * step] / 255));
      frame = requestAnimationFrame(loop);
    };
    loop();
    return () => cancelAnimationFrame(frame);
  }, [analyser, active, reduce]);

  return <canvas ref={canvasRef} aria-hidden="true" className="h-16 w-full max-w-md" />;
}
