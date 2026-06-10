import { FadeIn } from '../components/ui/FadeIn';
import portfolioData from '../data/portfolioData.json';

const CERTS = portfolioData.certifications;

export function CertificationsSection() {
  return (
    <section className="py-24 sm:py-32 px-5 sm:px-10 bg-[#0C0C0C]">
      <div className="max-w-6xl mx-auto">
        <FadeIn y={30}>
          <h2 className="text-[3rem] sm:text-[8vw] md:text-[100px] font-black uppercase leading-none tracking-tight hero-heading mb-16 sm:mb-24 text-center">
            Certifications
          </h2>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CERTS.map((cert, i) => (
            <FadeIn key={i} delay={i * 0.1} y={20}>
              <div className="group relative border border-primary/20 bg-background rounded-2xl p-8 hover:border-primary/50 transition-colors duration-500 h-full flex flex-col justify-center text-center">
                <div className="absolute inset-0 bg-gradient-to-tr from-primary/0 via-primary/5 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl" />
                <h3 className="text-xl font-bold uppercase tracking-wide text-primary relative z-10">{cert}</h3>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
