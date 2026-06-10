import { FadeIn } from '../components/ui/FadeIn';
import portfolioData from '../data/portfolioData.json';

const SKILLS = portfolioData.skills;

export function SkillsSection() {
  return (
    <section className="py-24 sm:py-32 px-5 sm:px-10 bg-background relative z-0">
      <div className="max-w-6xl mx-auto">
        <FadeIn y={30}>
          <h2 className="text-[3rem] sm:text-[8vw] md:text-[100px] font-black uppercase leading-none tracking-tight hero-heading mb-16 sm:mb-24 text-center">
            Technical Arsenal
          </h2>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {SKILLS.map((skillGroup, i) => (
            <FadeIn key={i} delay={i * 0.1} y={20}>
              <div className="group relative border border-primary/20 bg-primary/5 backdrop-blur-md rounded-3xl p-8 hover:bg-primary/10 transition-colors duration-500 overflow-hidden h-full">
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <h3 className="text-2xl font-bold uppercase tracking-widest text-primary mb-6 relative z-10">{skillGroup.category}</h3>
                <div className="flex flex-wrap gap-3 relative z-10">
                  {skillGroup.items.map(item => (
                    <span key={item} className="px-4 py-2 bg-background border border-primary/20 rounded-full text-sm font-medium tracking-wide">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
