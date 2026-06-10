import { FadeIn } from '../components/ui/FadeIn';
import portfolioData from '../data/portfolioData.json';

const PROJECTS = portfolioData.projects;

export function ProjectsSection() {
  return (
    <section id="projects" className="bg-background rounded-t-[40px] sm:rounded-t-[60px] -mt-10 px-5 sm:px-10 py-24 sm:py-32 relative z-10">
      <div className="max-w-6xl mx-auto">
        <FadeIn y={30}>
          <h2 className="text-[3rem] sm:text-[10vw] md:text-[120px] font-black uppercase leading-none tracking-tight hero-heading mb-20 text-center">
            Projects
          </h2>
        </FadeIn>

        <div className="flex flex-col gap-24 sm:gap-32">
          {PROJECTS.map((p, i) => (
            <div key={i} className="sticky top-24 md:top-32 border-2 border-primary/20 bg-background/80 backdrop-blur-xl rounded-[40px] p-6 sm:p-10 flex flex-col md:flex-row gap-10">
              <div className="w-full md:w-1/2 flex flex-col justify-between">
                <div>
                  <div className="text-[4rem] font-black hero-heading mb-4 leading-none">0{i + 1}</div>
                  <h3 className="text-3xl sm:text-4xl font-bold uppercase tracking-tight mb-6">{p.title}</h3>
                  <p className="text-primary/70 text-lg mb-8">{p.desc}</p>
                  <div className="flex flex-wrap gap-3 mb-10">
                    {p.tech.map(t => (
                      <span key={t} className="px-4 py-2 border border-primary/20 rounded-full text-sm font-medium">{t}</span>
                    ))}
                  </div>
                </div>
                <a href={p.link} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center border-2 border-primary text-primary px-8 py-4 rounded-full font-bold uppercase tracking-widest hover:bg-primary/10 transition-colors w-max">
                  Live Project
                </a>
              </div>
              <div className="w-full md:w-1/2 h-64 md:h-auto min-h-[300px] rounded-[30px] overflow-hidden">
                <img src={p.img} alt={p.title} className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-700 hover:scale-105" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
