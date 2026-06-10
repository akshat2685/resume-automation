import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';

const ITEMS = [
  "AI Agents", "Workflow Automation", "Lead Intelligence", "Chatbots", 
  "OCR Systems", "Python", "React", "Next.js", "Automation", 
  "Machine Learning", "CRM Integration", "Data Pipelines", 
  "Generative AI", "OpenAI APIs", "Agentic Workflows"
];

export function MarqueeSection() {
  const container = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: container, offset: ['start end', 'end start'] });
  
  const x1 = useTransform(scrollYProgress, [0, 1], [0, -1000]);
  const x2 = useTransform(scrollYProgress, [0, 1], [-1000, 0]);

  return (
    <section ref={container} className="py-24 sm:py-32 overflow-hidden bg-background relative border-y border-primary/5">
      <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-background to-transparent z-10" />
      <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-background to-transparent z-10" />
      
      <div className="flex flex-col gap-6 sm:gap-8">
        <motion.div style={{ x: x1 }} className="flex gap-4 sm:gap-6 whitespace-nowrap">
          {[...ITEMS, ...ITEMS].map((item, i) => (
            <div key={i} className="px-6 py-3 sm:px-8 sm:py-4 rounded-full border border-primary/10 bg-primary/5 backdrop-blur-sm text-primary/80 font-medium tracking-wide uppercase text-sm sm:text-base hover:bg-primary/10 hover:border-primary/30 hover:text-primary transition-all cursor-default">
              {item}
            </div>
          ))}
        </motion.div>
        
        <motion.div style={{ x: x2 }} className="flex gap-4 sm:gap-6 whitespace-nowrap">
          {[...ITEMS, ...ITEMS].reverse().map((item, i) => (
            <div key={i} className="px-6 py-3 sm:px-8 sm:py-4 rounded-full border border-primary/10 bg-primary/5 backdrop-blur-sm text-primary/80 font-medium tracking-wide uppercase text-sm sm:text-base hover:bg-primary/10 hover:border-primary/30 hover:text-primary transition-all cursor-default">
              {item}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
