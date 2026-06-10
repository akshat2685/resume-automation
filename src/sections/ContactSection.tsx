import { FadeIn } from '../components/ui/FadeIn';
import { Magnet } from '../components/ui/Magnet';
import { Mail, Link, Code } from 'lucide-react';

export function ContactSection() {
  return (
    <section id="contact" className="py-32 sm:py-48 px-5 sm:px-10 bg-[#0C0C0C] flex flex-col items-center justify-center text-center">
      <FadeIn y={30}>
        <h2 className="text-[10vw] sm:text-[8vw] md:text-[80px] font-black uppercase leading-none tracking-tight hero-heading mb-8">
          Let's Build Something<br />Intelligent
        </h2>
      </FadeIn>

      <FadeIn delay={0.2} y={20}>
        <p className="text-primary/70 text-xl sm:text-2xl font-light mb-16 max-w-2xl mx-auto">
          Interested in AI, automation, software development, or innovative technology projects? Let's connect.
        </p>
      </FadeIn>

      <FadeIn delay={0.4} y={20} className="flex flex-col sm:flex-row gap-6">
        <Magnet strength={0.2}>
          <a href="mailto:i.jain.akshat@gmail.com" className="flex items-center gap-3 bg-primary text-background px-10 py-5 rounded-full font-bold uppercase tracking-widest text-sm hover:scale-105 transition-transform">
            <Mail className="w-5 h-5" />
            Email Me
          </a>
        </Magnet>
        
        <Magnet strength={0.2}>
          <a href="https://www.linkedin.com/in/akshat-jain-02530a26a/" target="_blank" rel="noreferrer" className="flex items-center gap-3 border-2 border-primary/20 text-primary px-10 py-5 rounded-full font-bold uppercase tracking-widest text-sm hover:border-primary/50 transition-colors">
            <Link className="w-5 h-5" />
            LinkedIn
          </a>
        </Magnet>

        <Magnet strength={0.2}>
          <a href="https://github.com/akshat2685" target="_blank" rel="noreferrer" className="flex items-center gap-3 border-2 border-primary/20 text-primary px-10 py-5 rounded-full font-bold uppercase tracking-widest text-sm hover:border-primary/50 transition-colors">
            <Code className="w-5 h-5" />
            GitHub
          </a>
        </Magnet>
      </FadeIn>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="py-10 text-center border-t border-primary/10 bg-[#0C0C0C]">
      <div className="flex flex-col gap-2">
        <span className="text-primary font-bold uppercase tracking-widest text-lg">Akshat Jain</span>
        <span className="text-primary/50 text-sm tracking-widest uppercase">AI Engineer • 3D Creator • Automation Builder</span>
        <span className="text-primary/30 text-xs mt-4">© {new Date().getFullYear()} All Rights Reserved.</span>
      </div>
    </footer>
  );
}
