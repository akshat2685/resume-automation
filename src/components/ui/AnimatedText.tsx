import { motion, useScroll, useTransform, MotionValue } from 'framer-motion';
import { useRef } from 'react';

interface WordProps {
  word: string;
  progress: MotionValue<number>;
  range: [number, number];
}

function Word({ word, progress, range }: WordProps) {
  const opacity = useTransform(progress, range, [0.2, 1]);
  return (
    <span style={{ position: 'relative' }}>
      <span style={{ opacity: 0 }}>{word}</span>
      <motion.span style={{ opacity, position: 'absolute', left: 0, top: 0 }}>
        {word}
      </motion.span>
    </span>
  );
}

export function AnimatedText({ text, className }: { text: string; className?: string }) {
  const container = useRef<HTMLParagraphElement>(null);
  const { scrollYProgress } = useScroll({
    target: container,
    offset: ['start 0.8', 'start 0.25']
  });

  const words = text.split(" ");

  return (
    <p ref={container} className={className} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25em', justifyContent: 'center' }}>
      {words.map((word, i) => {
        const start = i / words.length;
        const end = start + (1 / words.length);
        return (
          <Word
            key={i}
            word={word}
            progress={scrollYProgress}
            range={[start, end]}
          />
        );
      })}
    </p>
  );
}
