import { useState, useEffect } from 'react';
import { FadeIn } from '../components/ui/FadeIn';
import { Magnet } from '../components/ui/Magnet';
import { Avatar3D } from '../components/ui/Avatar3D';
import { AvatarCreatorModal } from '../components/ui/AvatarCreatorModal';
import { ArrowRight, Terminal, Sparkles } from 'lucide-react';


export function HeroSection() {
  const [avatarUrl, setAvatarUrl] = useState<string>('');
  const [isCustomizerOpen, setIsCustomizerOpen] = useState(false);

  // Load avatar URL from localStorage on mount
  useEffect(() => {
    const savedUrl = localStorage.getItem('user_3d_avatar_url');
    if (savedUrl) {
      setAvatarUrl(savedUrl);
    }
  }, []);

  const handleAvatarCreated = (url: string) => {
    localStorage.setItem('user_3d_avatar_url', url);
    setAvatarUrl(url);
    setIsCustomizerOpen(false);
  };

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-5 sm:px-10 pt-20">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="z-10 max-w-7xl mx-auto w-full flex flex-col-reverse lg:flex-row items-center gap-10">
        
        {/* Left Side Text */}
        <div className="w-full lg:w-1/2 flex flex-col items-start text-left relative z-20">
          <FadeIn y={50}>
            <h1 className="text-[12vw] sm:text-[9vw] lg:text-[6vw] font-black uppercase leading-none tracking-tight hero-heading mb-6">
              Building AI Systems
              <br /> That Work.
            </h1>
          </FadeIn>

          <FadeIn delay={0.2} y={30}>
            <p className="text-primary/70 font-light text-lg sm:text-xl lg:text-2xl max-w-xl leading-relaxed mb-12">
              Computer Science Engineering student passionate about building AI-powered products, intelligent automation systems, OCR solutions, chatbots, and scalable software.
            </p>
          </FadeIn>

          <FadeIn delay={0.4} y={20} className="flex flex-col sm:flex-row gap-6 items-center">
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
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 divide-x divide-primary/10">
              <div className="flex flex-col gap-2">
                <span className="text-4xl font-black hero-heading">3+</span>
                <span className="text-xs uppercase tracking-widest text-primary/50">Major AI<br/>Projects</span>
              </div>
              <div className="flex flex-col gap-2 pl-8">
                <span className="text-4xl font-black hero-heading">10+</span>
                <span className="text-xs uppercase tracking-widest text-primary/50">Software<br/>Projects</span>
              </div>
              <div className="flex flex-col gap-2 pl-8 col-span-2 sm:col-span-1 border-t sm:border-t-0 sm:border-l border-primary/10 pt-8 sm:pt-0">
                <span className="text-4xl font-black hero-heading">2027</span>
                <span className="text-xs uppercase tracking-widest text-primary/50">B.Tech<br/>Graduation</span>
              </div>
            </div>
          </FadeIn>
        </div>

        {/* Right Side 3D Avatar */}
        <div className="w-full lg:w-1/2 h-[500px] lg:h-[800px] relative mt-10 lg:mt-0 z-10 flex flex-col items-center justify-center">
          <FadeIn delay={0.3} y={0} className="w-full h-full relative">
            <Avatar3D url={avatarUrl || undefined} />
          </FadeIn>
          
          {/* Customizer Button overlay */}
          <div className="absolute bottom-10 z-20">
            <Magnet strength={0.2}>
              <button 
                onClick={() => setIsCustomizerOpen(true)}
                className="group flex items-center gap-2 bg-[#D7E2EA]/10 hover:bg-[#D7E2EA] text-[#D7E2EA] hover:text-[#0C0C0C] border border-white/20 hover:border-[#D7E2EA] px-6 py-3 rounded-full font-medium uppercase tracking-widest text-xs transition-all duration-300 backdrop-blur-md shadow-2xl cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 group-hover:animate-pulse" />
                Customize Avatar
              </button>
            </Magnet>
          </div>
          
          <AvatarCreatorModal 
            isOpen={isCustomizerOpen} 
            onClose={() => setIsCustomizerOpen(false)} 
            onAvatarCreated={handleAvatarCreated}
          />
        </div>
        
      </div>
    </section>
  );
}
