import { HeroSection } from './sections/HeroSection'
import { MarqueeSection } from './sections/MarqueeSection'
import { AboutSection } from './sections/AboutSection'
import { SkillsSection } from './sections/SkillsSection'
import { ServicesSection } from './sections/ServicesSection'
import { ProjectsSection } from './sections/ProjectsSection'
import { CertificationsSection } from './sections/CertificationsSection'
import { CurrentlyBuildingSection } from './sections/CurrentlyBuildingSection'
import { ContactSection, Footer } from './sections/ContactSection'

function App() {
  return (
    <main className="bg-[#0C0C0C] text-[#D7E2EA] font-sans selection:bg-[#D7E2EA] selection:text-[#0C0C0C]">
      <HeroSection />
      <MarqueeSection />
      <AboutSection />
      <SkillsSection />
      <ServicesSection />
      <ProjectsSection />
      <CertificationsSection />
      <CurrentlyBuildingSection />
      <ContactSection />
      <Footer />
    </main>
  )
}

export default App
