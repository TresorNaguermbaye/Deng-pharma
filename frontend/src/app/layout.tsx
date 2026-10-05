import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/lib/auth";
import Providers from "./providers";
import PWAProvider from "@/components/PWAProvider";
import GlobalSearch from "@/components/GlobalSearch";
import FloatingChatWrapper from "@/components/FloatingChatWrapper";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DENG PHARMA - Gestion Pharmaceutique",
  description: "Plateforme SaaS intelligente de gestion pharmaceutique avec IA",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icons/icon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512x512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/icons/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "DENG PHARMA",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="antialiased bg-slate-50 dark:bg-slate-900 min-h-screen">
        <Providers>
          <AuthProvider>
            <PWAProvider> 
              <ThemeProvider>
                {children}
                <GlobalSearch />
                <FloatingChatWrapper />
                <Toaster richColors />
              </ThemeProvider>
            </PWAProvider>
          </AuthProvider>
        </Providers>
      </body>
    </html>
  );
}