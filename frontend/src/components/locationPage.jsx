// src/components/LocationPage.jsx
import React, { useState } from 'react';
import Header from './Header';
import LocationSelector from './LocationSelector';

export default function LocationPage({ onSelectLocation }) {
  const [lang, setLang] = useState('en');

  return (
    <div 
      className="min-h-screen w-full flex flex-col justify-between relative overflow-hidden bg-cover bg-center"
      style={{ backgroundImage: `url('/bgfarming.png')` }}
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-emerald-900/10 via-emerald-100/40 to-sky-100/50 pointer-events-none"></div>

      <Header lang={lang} setLang={setLang} />

      <main className="flex-1 flex items-center justify-center px-4 py-8 relative z-10">
        <LocationSelector onSelectLocation={onSelectLocation} lang={lang} />
      </main>

      <footer className="py-4 text-center text-xs text-emerald-900/70 font-medium relative z-10 bg-white/30 backdrop-blur-xs">
        TerraMind • Panchayat-level Weather Intelligence Platform, West Bengal
      </footer>
    </div>
  );
}