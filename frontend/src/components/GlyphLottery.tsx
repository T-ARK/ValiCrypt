import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { RotateCcw } from 'lucide-react';

interface GlyphLotteryProps {
  text: string;
  className?: string;
  replayable?: boolean;
}

const CYBER_GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*<>~+/=§±¥アカイエオカキクケサシスセタチツ";

export const GlyphLottery: React.FC<GlyphLotteryProps> = ({
  text,
  className = "",
  replayable = true,
}) => {
  const [displayedChars, setDisplayedChars] = useState<string[]>([]);
  const [lockedFlags, setLockedFlags] = useState<boolean[]>([]);
  const [isSpinning, setIsSpinning] = useState(false);
  const animationFrameRef = useRef<number | null>(null);

  // Group characters into words to preserve word boundaries on small mobile screens (320px+)
  const words = useMemo(() => {
    let globalIndex = 0;
    return text.split(' ').map((word) => {
      const chars = word.split('').map((char) => ({
        char,
        index: globalIndex++,
      }));
      globalIndex++; // Space offset
      return chars;
    });
  }, [text]);

  const startLottery = useCallback(() => {
    setIsSpinning(true);
    const chars = text.split("");

    // Initial random glyphs
    setDisplayedChars(
      chars.map((char) =>
        char === " " ? " " : CYBER_GLYPHS[Math.floor(Math.random() * CYBER_GLYPHS.length)]
      )
    );
    setLockedFlags(chars.map((char) => char === " "));

    const startTime = performance.now();
    const lockDelays = chars.map((char, index) => {
      if (char === " ") return 0;
      return 350 + index * 40;
    });

    let lastTick = 0;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      let allLocked = true;

      // Update glyphs every 35ms for smooth slot-reel spin
      if (now - lastTick > 35) {
        lastTick = now;

        setDisplayedChars(() =>
          chars.map((targetChar, index) => {
            if (targetChar === " ") return " ";
            if (elapsed >= lockDelays[index]) {
              return targetChar;
            }
            allLocked = false;
            return CYBER_GLYPHS[Math.floor(Math.random() * CYBER_GLYPHS.length)];
          })
        );

        setLockedFlags(
          chars.map((targetChar, index) => targetChar === " " || elapsed >= lockDelays[index])
        );
      }

      if (allLocked && elapsed > Math.max(...lockDelays)) {
        setDisplayedChars([...chars]);
        setLockedFlags(chars.map(() => true));
        setIsSpinning(false);
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }
      } else {
        animationFrameRef.current = requestAnimationFrame(tick);
      }
    };

    animationFrameRef.current = requestAnimationFrame(tick);
  }, [text]);

  useEffect(() => {
    startLottery();
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [startLottery]);

  return (
    <div className="relative inline-flex flex-col items-center group max-w-full">
      <div
        className={`font-heading tracking-tight select-none flex flex-wrap justify-center items-center gap-x-2 sm:gap-x-3.5 gap-y-1.5 max-w-full ${className}`}
      >
        {words.map((wordChars, wordIdx) => (
          <div key={wordIdx} className="inline-flex whitespace-nowrap items-center">
            {wordChars.map(({ index }) => {
              const char = displayedChars[index] || " ";
              const isLocked = lockedFlags[index];
              return (
                <span
                  key={index}
                  className={`inline-block transition-colors duration-150 min-w-[0.55em] text-center ${
                    isLocked
                      ? "text-white drop-shadow-[0_0_12px_rgba(217,70,239,0.8)]"
                      : "text-fuchsia-400 animate-pulse drop-shadow-[0_0_8px_rgba(168,85,247,0.9)] font-mono"
                  }`}
                >
                  {char}
                </span>
              );
            })}
          </div>
        ))}
      </div>

      {replayable && (
        <button
          type="button"
          onClick={startLottery}
          disabled={isSpinning}
          title="Re-spin Glyph Lottery"
          aria-label="Re-spin headline animation"
          className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-[11px] font-mono text-purple-300/70 hover:text-fuchsia-300 flex items-center space-x-1.5 px-3 py-1 rounded-md bg-[#0d061c]/80 border border-purple-500/20 active:scale-95"
        >
          <RotateCcw className={`w-3 h-3 ${isSpinning ? "animate-spin" : ""}`} />
          <span>Re-spin Headline</span>
        </button>
      )}
    </div>
  );
};
