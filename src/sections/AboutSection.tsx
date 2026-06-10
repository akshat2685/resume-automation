import { AnimatedText } from '../components/ui/AnimatedText';
import { FadeIn } from '../components/ui/FadeIn';

export function AboutSection() {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-5 sm:px-10 py-24 sm:py-32 relative">
      <div className="max-w-4xl mx-auto w-full text-center">
        <FadeIn y={30}>
          <h2 className="text-[3rem] sm:text-[10vw] md:text-[120px] font-black uppercase leading-none tracking-tight hero-heading mb-16 sm:mb-24">
            About Me
          </h2>
        </FadeIn>

        <AnimatedText 
          className="text-primary font-medium text-lg sm:text-2xl md:text-3xl leading-relaxed max-w-3xl mx-auto"
          text="I am Akshat Jain, a Computer Science Engineering student passionate about building AI-powered products, intelligent automation, and 3D experiences. My experience spans AI chatbots, OCR-based document processing, lead intelligence pipelines, and 3D modeling/rendering. I enjoy solving real-world business problems through smart automation and interactive visuals while continuously exploring emerging AI technologies. Let's build the future together."
        />
      </div>
    </section>
  );
}
