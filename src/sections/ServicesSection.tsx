import { FadeIn } from '../components/ui/FadeIn';
import portfolioData from '../data/portfolioData.json';

const SERVICES = portfolioData.services;

export function ServicesSection() {
  return (
    <section className="bg-white rounded-t-[40px] sm:rounded-t-[60px] px-5 sm:px-10 py-24 sm:py-32 text-[#0C0C0C]">
      <div className="max-w-5xl mx-auto">
        <FadeIn y={30}>
          <h2 className="text-[3rem] sm:text-[10vw] md:text-[120px] font-black uppercase leading-none tracking-tight text-center mb-20 sm:mb-28">
            What I Build
          </h2>
        </FadeIn>

        <div className="flex flex-col">
          {SERVICES.map((s, i) => (
            <FadeIn key={i} delay={i * 0.1} y={30} className="border-t border-[#0C0C0C]/10 py-10 sm:py-14 flex flex-col md:flex-row gap-8 md:gap-16 items-start md:items-center">
              <div className="text-[3rem] sm:text-[6vw] md:text-[80px] font-black leading-none opacity-20 w-32 shrink-0">
                0{i + 1}
              </div>
              <div className="flex flex-col gap-4">
                <h3 className="text-xl sm:text-2xl md:text-3xl font-bold uppercase tracking-wide">{s.title}</h3>
                <p className="text-base sm:text-lg text-[#0C0C0C]/60 leading-relaxed max-w-2xl font-medium">
                  {s.desc}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
