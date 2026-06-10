import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, Link, Palette } from 'lucide-react';

interface AvatarCreatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAvatarCreated: (url: string) => void;
}

export function AvatarCreatorModal({ isOpen, onClose, onAvatarCreated }: AvatarCreatorModalProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'create' | 'link'>('create');
  const [manualUrl, setManualUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    setErrorMsg('');

    const handleMessage = (event: MessageEvent) => {
      let json;
      try {
        json = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
      } catch (err) {
        return;
      }

      if (json?.source !== 'readyplayerme') return;

      if (json.eventName === 'v1.frame.ready') {
        setIsLoading(false);
        if (iframeRef.current?.contentWindow) {
          iframeRef.current.contentWindow.postMessage(
            JSON.stringify({
              target: 'readyplayerme',
              type: 'subscribe',
              eventName: 'v1.**',
            }),
            '*'
          );
        }
      }

      if (json.eventName === 'v1.avatar.exported') {
        const avatarUrl = json.data?.url;
        if (avatarUrl) {
          onAvatarCreated(avatarUrl);
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [isOpen, onAvatarCreated]);

  const handleIframeLoad = () => {
    // Native iframe onLoad event. We set isLoading to false in case v1.frame.ready didn't fire
    // or if the page failed to load (to show browser's offline/error page instead of our spinner).
    // We wait 1 second to give the frame API a chance to run first.
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualUrl.trim()) {
      setErrorMsg('Please enter a URL');
      return;
    }
    if (!manualUrl.toLowerCase().endsWith('.glb') && !manualUrl.includes('readyplayer.me')) {
      setErrorMsg('URL should point to a 3D model (.glb file)');
      return;
    }
    onAvatarCreated(manualUrl.trim());
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 md:p-10">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
          />

          {/* Modal Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="relative w-full max-w-4xl h-[80vh] bg-[#0C0C0C] border border-white/10 rounded-2xl overflow-hidden shadow-2xl z-10 flex flex-col"
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between px-6 py-4 border-b border-white/5 bg-black/40 gap-4">
              <div>
                <h3 className="text-lg font-bold text-[#D7E2EA] tracking-wide uppercase font-sans">
                  3D Avatar Settings
                </h3>
                <p className="text-xs text-[#D7E2EA]/50 font-sans mt-0.5">
                  Set up your personalized face for the website's 3D viewer.
                </p>
              </div>
              
              {/* Tabs */}
              <div className="flex bg-white/5 p-1 rounded-lg border border-white/10 self-start sm:self-center">
                <button
                  onClick={() => setActiveTab('create')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium uppercase tracking-wider transition-colors ${
                    activeTab === 'create'
                      ? 'bg-white/15 text-white'
                      : 'text-[#D7E2EA]/60 hover:text-white'
                  }`}
                >
                  <Palette className="w-3.5 h-3.5" />
                  Creator Studio
                </button>
                <button
                  onClick={() => setActiveTab('link')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium uppercase tracking-wider transition-colors ${
                    activeTab === 'link'
                      ? 'bg-white/15 text-white'
                      : 'text-[#D7E2EA]/60 hover:text-white'
                  }`}
                >
                  <Link className="w-3.5 h-3.5" />
                  Paste GLB Link
                </button>
              </div>

              <button
                onClick={onClose}
                className="absolute top-4 right-6 text-[#D7E2EA]/50 hover:text-[#D7E2EA] p-1.5 rounded-lg hover:bg-white/5 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tab Body */}
            <div className="flex-1 w-full h-full relative bg-[#0C0C0C]">
              {activeTab === 'create' ? (
                <>
                  {isLoading && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0C0C0C] z-10 gap-4 px-6 text-center">
                      <Loader2 className="w-8 h-8 animate-spin text-[#BBCCD7]" />
                      <div>
                        <p className="text-sm text-[#D7E2EA]/85 font-sans font-medium">
                          Connecting to Ready Player Me...
                        </p>
                        <p className="text-xs text-[#D7E2EA]/50 font-sans mt-2 max-w-sm">
                          If this takes too long, you might have network restrictions. Try using the "Paste GLB Link" tab instead.
                        </p>
                      </div>
                    </div>
                  )}
                  <iframe
                    ref={iframeRef}
                    src="https://demo.readyplayer.me/avatar?frameApi&clearCache"
                    className="w-full h-full border-none"
                    allow="camera *; microphone *; clipboard-write"
                    onLoad={handleIframeLoad}
                  />
                </>
              ) : (
                <div className="w-full h-full flex items-center justify-center p-6 sm:p-12">
                  <form onSubmit={handleManualSubmit} className="w-full max-w-md flex flex-col gap-6">
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold uppercase tracking-wider text-[#D7E2EA]/80">
                        Link Your 3D Avatar
                      </h4>
                      <p className="text-xs text-[#D7E2EA]/50 leading-relaxed">
                        If you've already created an avatar and have its `.glb` URL, or generated one on readyplayer.me in your normal browser, paste the direct link below.
                      </p>
                    </div>

                    <div className="space-y-4">
                      <div className="relative">
                        <input
                          type="url"
                          placeholder="https://models.readyplayer.me/your-avatar-id.glb"
                          value={manualUrl}
                          onChange={(e) => {
                            setManualUrl(e.target.value);
                            setErrorMsg('');
                          }}
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-[#BBCCD7]/50 focus:bg-white/10 transition-all font-sans"
                        />
                      </div>
                      
                      {errorMsg && (
                        <p className="text-red-400 text-xs font-sans">
                          {errorMsg}
                        </p>
                      )}
                    </div>

                    <button
                      type="submit"
                      className="w-full bg-[#D7E2EA] hover:bg-white text-[#0C0C0C] py-3.5 rounded-xl font-semibold text-xs uppercase tracking-wider transition-colors cursor-pointer"
                    >
                      Apply 3D Avatar
                    </button>
                    
                    <div className="text-center">
                      <a 
                        href="https://readyplayer.me" 
                        target="_blank" 
                        rel="noreferrer" 
                        className="text-xs text-[#D7E2EA]/40 hover:text-[#D7E2EA]/70 underline transition-colors"
                      >
                        Go to readyplayer.me in a new tab
                      </a>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
