// src/components/Header.jsx
import React from 'react';

export default function Header({ lang, setLang }) {
  const subtitles = {
    en: "Smarter Weather, Better Farming",
    bn: "স্মার্ট আবহাওয়া, উন্নত চাষবাস",
    hi: "बेहतर मौसम, बेहतर खेती"
  };

  const aboutTexts = {
    en: "About",
    bn: "আমাদের সম্পর্কে",
    hi: "हमारे बारे में"
  };

  return (
    <header className="w-full py-5 px-6 md:px-12 flex justify-between items-center bg-transparent relative z-10">
      <div className="flex flex-col">
        {/* PanchMausam: #22C55E */}
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight" style={{ color: '#22C55E' }}>
          PanchMausam
        </h1>
        {/* Smarter Weather...: #0EA5E9 */}
        <p className="text-xs md:text-sm font-semibold tracking-wide" style={{ color: '#0EA5E9' }}>
          {subtitles[lang] || subtitles.en}
        </p>
      </div>
      
      <div className="flex items-center gap-3 text-sm font-medium">
        {/* Language dropdown button & text: #163A32 */}
        <div className="relative">
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="px-4 py-2 bg-white/90 hover:bg-white rounded-full shadow-sm border border-emerald-200 transition font-bold cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none pr-8"
            style={{ color: '#163A32' }}
          >
            <option value="en">🌐 English</option>
            <option value="bn">🌐 বাংলা</option>
            <option value="hi">🌐 हिन्दी</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-xs" style={{ color: '#163A32' }}>
            ▼
          </div>
        </div>

        {/* About: #24527A */}
        <button 
          className="hidden sm:inline-block px-4 py-2 bg-white/60 hover:bg-white/90 rounded-full transition font-medium"
          style={{ color: '#24527A' }}
        >
          {aboutTexts[lang] || aboutTexts.en}
        </button>
      </div>
    </header>
  );
}