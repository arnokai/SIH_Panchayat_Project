// src/components/LocationSelector.jsx
import React, { useState } from 'react';
import { locationHierarchy, panchayatIdMap, DEFAULT_PANCHAYAT_ID } from '../data/mockLocations';

export default function LocationSelector({ onSelectLocation, lang = 'en' }) {
  const districts = Object.keys(locationHierarchy);
  
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedBlock, setSelectedBlock] = useState('');
  const [selectedPanchayat, setSelectedPanchayat] = useState('');

  const blocks = selectedDistrict ? Object.keys(locationHierarchy[selectedDistrict].blocks) : [];
  const panchayats = (selectedDistrict && selectedBlock) 
    ? locationHierarchy[selectedDistrict].blocks[selectedBlock] 
    : [];

  const t = {
    en: {
      title: "Select Your Location",
      subtitle: "Get accurate weather and advisory for your Panchayat",
      district: "District",
      selectDistrict: "Select District",
      block: "Block",
      selectBlock: "Select Block",
      panchayat: "Panchayat",
      selectPanchayat: "Select Panchayat",
      currentLocation: "Use My Current Location",
      button: "VIEW FORECAST",
      alert: "Please select your Panchayat to view the forecast."
    },
    bn: {
      title: "আপনার অবস্থান নির্বাচন করুন",
      subtitle: "আপনার পঞ্চায়েতের জন্য সঠিক আবহাওয়া এবং কৃষি পরামর্শ পান",
      district: "জেলা",
      selectDistrict: "জেলা নির্বাচন করুন",
      block: "ব্লক",
      selectBlock: "ব্লক নির্বাচন করুন",
      panchayat: "গ্রাম পঞ্চায়েত",
      selectPanchayat: "পঞ্চায়েত নির্বাচন করুন",
      currentLocation: "আমার বর্তমান অবস্থান ব্যবহার করুন",
      button: "পূর্বাভাস দেখুন",
      alert: "আবহাওয়া দেখতে অনুগ্রহ করে আপনার পঞ্চায়েত নির্বাচন করুন।"
    },
    hi: {
      title: "अपना स्थान चुनें",
      subtitle: "अपनी पंचायत के लिए सटीक मौसम और कृषि सलाह प्राप्त करें",
      district: "जिला",
      selectDistrict: "जिला चुनें",
      block: "ब्लॉक",
      selectBlock: "ब्लॉक चुनें",
      panchayat: "पंचायत",
      selectPanchayat: "पंचायत चुनें",
      currentLocation: "मेरे वर्तमान स्थान का उपयोग करें",
      button: "पूर्वानुमान देखें",
      alert: "पूर्वानुमान देखने के लिए कृपया अपनी पंचायत चुनें।"
    }
  };

  const currentT = t[lang] || t.en;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedPanchayat) {
      alert(currentT.alert);
      return;
    }
    const panchayatId = panchayatIdMap[selectedPanchayat] || DEFAULT_PANCHAYAT_ID;
    onSelectLocation({
      district: selectedDistrict,
      block: selectedBlock,
      panchayat: selectedPanchayat,
      panchayat_id: panchayatId
    });
  };

  return (
    <div className="w-full max-w-lg glass-card rounded-3xl p-6 md:p-8 relative z-10">
      <div className="mb-6">
        {/* Select your location title: #163A32 */}
        <h2 className="text-xl md:text-2xl font-bold tracking-tight" style={{ color: '#163A32' }}>
          {currentT.title}
        </h2>
        {/* Get accurate weather subtitle: #24527A */}
        <p className="text-sm mt-1 font-medium" style={{ color: '#24527A' }}>
          {currentT.subtitle}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* District */}
        <div>
          {/* Dropdown label: #26734D */}
          <label className="block text-xs font-bold uppercase tracking-wider mb-1" style={{ color: '#26734D' }}>
            {currentT.district}
          </label>
          <div className="relative">
            <select
              value={selectedDistrict}
              onChange={(e) => { setSelectedDistrict(e.target.value); setSelectedBlock(''); setSelectedPanchayat(''); }}
              className="w-full p-3.5 bg-white/90 border border-slate-200 rounded-2xl text-slate-800 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer shadow-xs text-sm font-medium"
            >
              <option value="">{currentT.selectDistrict}</option>
              {districts.map((dist) => (
                <option key={dist} value={dist}>{dist}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 text-xs">▼</div>
          </div>
        </div>

        {/* Block */}
        <div>
          {/* Dropdown label: #26734D */}
          <label className="block text-xs font-bold uppercase tracking-wider mb-1" style={{ color: '#26734D' }}>
            {currentT.block}
          </label>
          <div className="relative">
            <select
              value={selectedBlock}
              onChange={(e) => { setSelectedBlock(e.target.value); setSelectedPanchayat(''); }}
              disabled={!selectedDistrict}
              className="w-full p-3.5 bg-white/90 border border-slate-200 rounded-2xl text-slate-800 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer shadow-xs text-sm font-medium disabled:bg-slate-100 disabled:cursor-not-allowed"
            >
              <option value="">{currentT.selectBlock}</option>
              {blocks.map((blk) => (
                <option key={blk} value={blk}>{blk}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 text-xs">▼</div>
          </div>
        </div>

        {/* Panchayat */}
        <div>
          {/* Dropdown label: #26734D */}
          <label className="block text-xs font-bold uppercase tracking-wider mb-1" style={{ color: '#26734D' }}>
            {currentT.panchayat}
          </label>
          <div className="relative">
            <select
              value={selectedPanchayat}
              onChange={(e) => setSelectedPanchayat(e.target.value)}
              disabled={!selectedBlock}
              className="w-full p-3.5 bg-white/90 border border-slate-200 rounded-2xl text-slate-800 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer shadow-xs text-sm font-medium disabled:bg-slate-100 disabled:cursor-not-allowed"
            >
              <option value="">{currentT.selectPanchayat}</option>
              {panchayats.map((pan) => (
                <option key={pan} value={pan}>{pan}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 text-xs">▼</div>
          </div>
        </div>

        {/* Use My Current Location */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => { setSelectedDistrict("North 24 Parganas"); setSelectedBlock("Amdanga"); setSelectedPanchayat("AMDANGA"); }}
            className="text-xs font-bold flex items-center gap-1.5 transition cursor-pointer"
            style={{ color: '#24527A' }}
          >
            {/* Location Icon: #E51F1F */}
            <span style={{ color: '#E51F1F' }}>📍</span> {currentT.currentLocation}
          </button>
        </div>

        {/* View Forecast Button: #0EA5E9 */}
        <div className="pt-4">
          <button
            type="submit"
            className="w-full py-4 px-6 text-white font-bold rounded-2xl shadow-lg transition flex items-center justify-between group cursor-pointer text-base tracking-wide"
            style={{ backgroundColor: '#0EA5E9', boxShadow: '0 10px 25px rgba(14, 165, 233, 0.25)' }}
          >
            <span>{currentT.button}</span>
            <span className="transform group-hover:translate-x-1.5 transition-transform text-lg">&rarr;</span>
          </button>
        </div>
      </form>
    </div>
  );
}