import { FadeIn } from '../components/ui/FadeIn';
import { Magnet } from '../components/ui/Magnet';
import { ArrowRight, Terminal } from 'lucide-react';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-5 sm:px-10 pt-20">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="z-10 max-w-4xl mx-auto w-full flex flex-col items-center text-center relative z-20">
        
        <div className="w-full flex flex-col items-center justify-center relative z-20">
          <FadeIn y={50}>
            <h1 className="text-[12vw] sm:text-[9vw] lg:text-[6vw] font-black uppercase leading-none tracking-tight hero-heading mb-6">
              Building AI Systems
              <br /> That Work.
            </h1>
          </FadeIn>

          <FadeIn delay={0.2} y={30}>
            <p className="text-primary/70 font-light text-lg sm:text-xl lg:text-2xl max-w-2xl leading-relaxed mb-12">
              Computer Science Engineering student passionate about building AI-powered products, intelligent automation systems, OCR solutions, chatbots, and scalable software.
            </p>
          </FadeIn>

          <FadeIn delay={0.4} y={20} className="flex flex-col sm:flex-row gap-6 items-center justify-center">
            <Magnet strength={0.2}>
              <a href="#contact" className="group flex items-center gap-2 bg-primary text-background px-8 py-4 rounded-full font-medium uppercase tracking-widest text-sm hover:bg-white transition-colors">
                Let's Build AI
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </a>
            </Magnet>
            <Magnet strength={0.2}>
              <a href="#projects" className="group flex items-center gap-2 border-2 border-primary/20 text-primary px-8 py-4 rounded-full font-medium uppercase tracking-widest text-sm hover:border-primary/40 transition-colors bg-background/50 backdrop-blur-sm">
                <Terminal className="w-4 h-4" />
                View Projects
              </a>
            </Magnet>
          </FadeIn>

          {/* Metrics */}
          <FadeIn delay={0.6} y={20} className="w-full mt-20 border-t border-primary/10 pt-10">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 justify-items-center">
              <div className="flex flex-col items-center gap-2">
                <span className="text-4xl font-black hero-heading">3+</span>
                <span className="text-xs uppercase tracking-widest text-primary/50 text-center">Major AI<br/>Projects</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <span className="text-4xl font-black hero-heading">10+</span>
                <span className="text-xs uppercase tracking-widest text-primary/50 text-center">Software<br/>Projects</span>
              </div>
              <div className="flex flex-col items-center gap-2 col-span-2 sm:col-span-1 pt-8 sm:pt-0">
                <span className="text-4xl font-black hero-heading">2027</span>
                <span className="text-xs uppercase tracking-widest text-primary/50 text-center">B.Tech<br/>Graduation</span>
              </div>
            </div>
          </FadeIn>
        </div>
        
      </div>
    </section>
  );
}
