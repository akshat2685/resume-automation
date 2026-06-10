import { Canvas } from '@react-three/fiber';
import { useGLTF, OrbitControls, ContactShadows, Float, useTexture } from '@react-three/drei';
import { Suspense, useEffect, Component } from 'react';
import type { ReactNode } from 'react';
import * as THREE from 'three';

class ErrorBoundary extends Component<{children: ReactNode, fallback: ReactNode}, {hasError: boolean}> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error) { console.error("Avatar failed to load:", error); }
  render() { return this.state.hasError ? this.props.fallback : this.props.children; }
}

function WireframeIcosahedron() {
  return (
    <Float speed={2} rotationIntensity={2} floatIntensity={2}>
      <mesh position={[0, 0, 0]}>
        <icosahedronGeometry args={[1.5, 0]} />
        <meshStandardMaterial color="#646973" wireframe />
      </mesh>
    </Float>
  );
}

function AvatarImageCard() {
  const texture = useTexture('/avatar.png');
  return (
    <Float speed={1.5} rotationIntensity={1} floatIntensity={1}>
      <group position={[0, 0.2, 0]}>
        {/* Soft shadow plane behind card */}
        <mesh position={[0, 0, -0.05]} scale={[2.5, 4.4, 1]}>
          <planeGeometry />
          <meshBasicMaterial color="#000000" transparent opacity={0.5} />
        </mesh>
        
        {/* Main Image Card with your face avatar */}
        <mesh scale={[2.5, 4.4, 1]}>
          <planeGeometry />
          <meshBasicMaterial map={texture} transparent={true} />
        </mesh>

        {/* Premium glowing glassmorphism border */}
        <mesh position={[0, 0, -0.01]} scale={[2.54, 4.44, 1]}>
          <planeGeometry />
          <meshBasicMaterial color="#BBCCD7" transparent opacity={0.15} wireframe />
        </mesh>
      </group>
    </Float>
  );
}

function FallbackShape() {
  return (
    <Suspense fallback={<WireframeIcosahedron />}>
      <AvatarImageCard />
    </Suspense>
  );
}



interface ModelProps {
  url: string;
}

function Model({ url }: ModelProps) {
  const { scene } = useGLTF(url);
  
  // Fix material issues and rotate arms down
  useEffect(() => {
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
      if (child.name === 'LeftArm') {
        child.rotation.x = 1.35;
        child.rotation.y = 0;
        child.rotation.z = 0.25;
      }
      if (child.name === 'RightArm') {
        child.rotation.x = 1.35;
        child.rotation.y = 0;
        child.rotation.z = -0.25;
      }
    });
  }, [scene]);
  
  return <primitive object={scene} scale={4.5} position={[0, -6.1, 0]} />;
}

export function Avatar3D({ url = "/avatar.glb" }: { url?: string }) {
  const showModel = !!url;

  return (
    <div className="w-full h-full absolute inset-0 cursor-grab active:cursor-grabbing">
      <Canvas shadows camera={{ position: [0, 0, 5], fov: 50 }}>
        <Suspense fallback={<WireframeIcosahedron />}>
          {showModel ? (
            <ErrorBoundary fallback={<FallbackShape />}>
              {/* Local offline lighting setup */}
              <ambientLight intensity={0.65} />
              <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow shadow-bias={-0.0001} />
              <directionalLight position={[-5, 5, -5]} intensity={0.4} />
              <pointLight position={[0, 4, 3]} intensity={0.3} />
              
              <Model url={url} />
              
              <ContactShadows position={[0, -2.5, 0]} opacity={0.6} scale={10} blur={2} far={4} color="#000000" />
            </ErrorBoundary>
          ) : (
            <FallbackShape />
          )}
        </Suspense>
        <OrbitControls 
          enablePan={false} 
          enableZoom={false} 
          minPolarAngle={Math.PI / 3} 
          maxPolarAngle={Math.PI / 2} 
          autoRotate
          autoRotateSpeed={1}
        />
      </Canvas>
    </div>
  );
}
