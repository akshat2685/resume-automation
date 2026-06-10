import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';

export function Magnet({ children, padding = 100, strength = 0.5, className }: { children: React.ReactNode, padding?: number, strength?: number, className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const { clientX, clientY } = e;
    const { height, width, left, top } = ref.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    
    // Check if mouse is within padding
    const distanceX = Math.abs(clientX - centerX);
    const distanceY = Math.abs(clientY - centerY);
    
    if (distanceX < (width / 2 + padding) && distanceY < (height / 2 + padding)) {
      setPosition({
        x: (clientX - centerX) * strength,
        y: (clientY - centerY) * strength
      });
    } else {
      setPosition({ x: 0, y: 0 });
    }
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: "spring", stiffness: 150, damping: 15, mass: 0.1 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
