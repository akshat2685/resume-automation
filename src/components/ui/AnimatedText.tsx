import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';

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
        const opacity = useTransform(scrollYProgress, [start, end], [0.2, 1]);
        return (
          <span key={i} style={{ position: 'relative' }}>
            <span style={{ opacity: 0 }}>{word}</span>
            <motion.span style={{ opacity, position: 'absolute', left: 0, top: 0 }}>
              {word}
            </motion.span>
          </span>
        );
      })}
    </p>
  );
}
