import { FadeIn } from '../components/ui/FadeIn';
import portfolioData from '../data/portfolioData.json';

const BUILDING = portfolioData.currentlyBuilding;

export function CurrentlyBuildingSection() {
  return (
    <section className="py-24 sm:py-32 px-5 sm:px-10 bg-background border-y border-primary/10 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[500px] bg-primary/5 blur-[100px] rounded-full pointer-events-none" />
      
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <FadeIn y={30}>
          <h2 className="text-xl sm:text-2xl font-bold uppercase tracking-[0.2em] text-primary/60 mb-12">
            Founder Mode: Currently Building
          </h2>
        </FadeIn>

        <div className="flex flex-wrap justify-center gap-4 sm:gap-6">
          {BUILDING.map((item, i) => (
            <FadeIn key={item} delay={i * 0.1} y={20}>
              <div className="px-6 py-4 sm:px-8 sm:py-5 bg-background border border-primary/20 rounded-2xl text-lg sm:text-xl font-medium tracking-wide shadow-[0_0_15px_rgba(215,226,234,0.05)] hover:shadow-[0_0_25px_rgba(215,226,234,0.15)] hover:border-primary/40 transition-all duration-300">
                {item}
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
