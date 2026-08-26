import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ✅ AJOUT OBLIGATOIRE POUR LE DOCKER (standalone output)
  output: 'standalone',

  // 👇 Le reste de ta configuration existante (si tu en as)
  // Exemple : images, reactStrictMode, etc.
  reactStrictMode: true,
  images: {
    domains: ['localhost'], // adapte si besoin
  },
  // ... tes autres options
};

export default nextConfig;