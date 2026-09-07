"use client";

import { useEffect, useState } from "react";

export default function Logo({ className = "w-8 h-8 rounded-xl object-cover" }: { className?: string }) {
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/auth/pharmacy-logo/')
      .then((res) => res.json())
      .then((data) => setLogoUrl(data.logo_url))
      .catch(() => setLogoUrl(null));
  }, []);

  if (logoUrl) {
    return <img src={logoUrl} alt="Logo pharmacie" className={className} />;
  }

  // Fallback
  return (
    <div className={`${className} bg-[#0ABAB5] flex items-center justify-center font-bold text-white`}>
      <img src={"https://res.cloudinary.com/dyx3vcyzp/image/upload/v1788107048/logo.png"} alt="Logo pharmacie" className={className} />
    </div>
  );
}