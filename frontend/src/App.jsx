// src/App.jsx
import React, { useState, useEffect } from 'react';
import LocationSelector from './components/LocationSelector';
import ForecastView from './ForecastView';
import AdvisoryView from './AdvisoryView';
import './App.css';

export default function App() {
  const [locationData, setLocationData] = useState(() => {
    const saved = localStorage.getItem('terramind_location');
    return saved ? JSON.parse(saved) : null;
  });

  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('home'); 
  const [lang, setLang] = useState('bn'); // 'en', 'bn', 'hi'

  const handleSelectLocation = (locInfo) => {
    setLocationData(locInfo);
    localStorage.setItem('terramind_location', JSON.stringify(locInfo));
  };

  const handleResetLocation = () => {
    localStorage.removeItem('terramind_location');
    setLocationData(null);
    setForecast(null);
  };

  // Complete multilingual dictionary for all UI text across the entire app
  const dict = {
    en: {
      tagline: "Smarter Weather, Better Farming",
      about: "About",
      online: "Online",
      offlineMode: "Offline Mode",
      cachedData: "Showing cached data",
      updated: "Updated",
      changeLocation: "Change Location",
      home: "Home",
      forecast: "Forecast",
      map: "Map",
      advisory: "Advisory",
      more: "More",
      currentWeather: "Current Weather",
      feelsLike: "Feels like",
      temperature: "Temperature",
      rainProb: "Rain Prob.",
      rainfall: "Rainfall",
      humidity: "Humidity",
      agroAdvisory: "Agro Advisory",
      highPriority: "High Priority",
      listen: "Listen",
      fiveDayForecast: "5-Day Forecast",
      viewDetails: "View Details",
      rainAlert: "Light to moderate rain is expected in your area. Keep an umbrella when going outside.",
      forecastComparisonMap: "Forecast Comparison Map",
      mapSubtitle: "See how the forecast varies across Panchayats within a Block.",
      district: "District",
      block: "Block",
      panchayat: "Panchayat",
      allPanchayats: "All Panchayats",
      blockLevelRef: "Block Level (Amdanga)",
      referenceAvg: "Reference / Average",
      panchayatLevel: "Panchayat Level",
      forecastRiskLevel: "Forecast / Risk Level",
      low: "Low",
      moderate: "Moderate",
      high: "High",
      veryHigh: "Very High",
      mapNotice: "Block-level forecast is an average (reference). Individual panchayats may have distinct forecasts.",
      returnHome: "Return to Home Dashboard",
      viewSection: "section of PanchMausam."
    },
    bn: {
      tagline: "স্মার্ট আবহাওয়া, উন্নত কৃষি",
      about: "সম্পর্কিত",
      online: "অনলাইন",
      offlineMode: "অফলাইন মোড",
      cachedData: "ক্যাশে থাকা তথ্য দেখানো হচ্ছে",
      updated: "আপডেট",
      changeLocation: "অবস্থান পরিবর্তন করুন",
      home: "হোম",
      forecast: "পূর্বাভাস",
      map: "ম্যাপ",
      advisory: "পরামর্শ",
      more: "আরও",
      currentWeather: "এখনকার আবহাওয়া",
      feelsLike: "অনুভূত",
      temperature: "তাপমাত্রা",
      rainProb: "বৃষ্টি সম্ভাবনা",
      rainfall: "বৃষ্টিপাত",
      humidity: "আর্দ্রতা",
      agroAdvisory: "কৃষি পরামর্শ",
      highPriority: "উচ্চ অগ্রাধিকার",
      listen: "শুনুন",
      fiveDayForecast: "৫ দিনের পূর্বাভাস",
      viewDetails: "বিস্তারিত দেখুন",
      rainAlert: "আপনার এলাকায় হালকা থেকে মাঝারি বৃষ্টির সম্ভাবনা রয়েছে। বাইরে যাওয়ার সময় ছাতা সাথে রাখুন।",
      forecastComparisonMap: "পূর্বাভাস তুলনা মানচিত্র",
      mapSubtitle: "একটি ব্লকের অধীনে বিভিন্ন পঞ্চায়েতের আবহাওয়ার পূর্বাভাস কীভাবে পরিবর্তিত হয় তা দেখুন।",
      district: "জেলা",
      block: "ব্লক",
      panchayat: "পঞ্চায়েত",
      allPanchayats: "সকল পঞ্চায়েত",
      blockLevelRef: "ব্লক স্তর (আমডাঙা)",
      referenceAvg: "রেফারেন্স / গড়",
      panchayatLevel: "পঞ্চায়েত স্তর",
      forecastRiskLevel: "পূর্বাভাস / ঝুঁকির মাত্রা",
      low: "কম",
      moderate: "মাঝারি",
      high: "বেশি",
      veryHigh: "খুব বেশি",
      mapNotice: "ব্লক স্তরের পূর্বাভাসটি গড় মান (রেফারেন্স)। প্রতিটি পঞ্চায়েতের জন্য আলাদা পূর্বাভাস থাকতে পারে।",
      returnHome: "হোম ড্যাশবোর্ডে ফিরে যান",
      viewSection: "সেকশনটি দেখছেন।"
    },
    hi: {
      tagline: "बेहतर मौसम, उन्नत खेती",
      about: "परिचय",
      online: "ऑनलाइन",
      offlineMode: "ऑफ़लाइन मोड",
      cachedData: "कैश्ड डेटा दिखाया जा रहा है",
      updated: "अपडेट",
      changeLocation: "स्थान बदलें",
      home: "होम",
      forecast: "पूर्वानुमान",
      map: "नक्शा",
      advisory: "सलाह",
      more: "और अधिक",
      currentWeather: "वर्तमान मौसम",
      feelsLike: "महसूस होता है",
      temperature: "तापमान",
      rainProb: "बारिश की संभावना",
      rainfall: "वर्षा",
      humidity: "आर्द्रता",
      agroAdvisory: "कृषि सलाह",
      highPriority: "उच्च प्राथमिकता",
      listen: "सुनें",
      fiveDayForecast: "5-दिन का पूर्वानुमान",
      viewDetails: "विस्तृत देखें",
      rainAlert: "आपके क्षेत्र में हल्की से मध्यम बारिश की संभावना है। बाहर जाते समय छाता साथ रखें।",
      forecastComparisonMap: "पूर्वानुमान तुलना नक्शा",
      mapSubtitle: "देखें कि एक ब्लॉक के भीतर विभिन्न पंचायतों में पूर्वानुमान कैसे भिन्न होता है।",
      district: "जिला",
      block: "ब्लॉक",
      panchayat: "पंचायत",
      allPanchayats: "सभी पंचायतें",
      blockLevelRef: "ब्लॉक स्तर (आमडांगा)",
      referenceAvg: "संदर्भ / औसत",
      panchayatLevel: "पंचायत स्तर",
      forecastRiskLevel: "पूर्वानुमान / जोखिम स्तर",
      low: "कम",
      moderate: "मध्यम",
      high: "अधिक",
      veryHigh: "बहुत अधिक",
      mapNotice: "ब्लॉक-स्तरीय पूर्वानुमान एक औसत (संदर्भ) है। प्रत्येक पंचायत का अलग पूर्वानुमान हो सकता है।",
      returnHome: "होम डैशबोर्ड पर लौटें",
      viewSection: "खंड देख रहे हैं।"
    }
  };

  const t = dict[lang] || dict.en;

  useEffect(() => {
    if (!locationData) return;
    const panchayatId = locationData.panchayat_id || "107778";
    setLoading(true);

    fetch(`http://127.0.0.1:8000/v1/forecast?panchayat_id=${panchayatId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch weather forecast data from server.");
        return res.json();
      })
      .then((data) => {
        setForecast(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn("Backend API fallback sample active:", err);
        setForecast({
          panchayat_id: panchayatId,
          panchayat_name: locationData.panchayat || "AMDANGA",
          block: locationData.block || "Amdanga",
          district: locationData.district || "North 24 Parganas",
          updated_at: "8:30 AM",
          current: {
            condition_bn: "আংশিক মেঘলা",
            condition_en: "Partly Cloudy",
            temp: 28,
            feels_like: 31,
            rain_prob: 40,
            rain_mm: 2.4,
            humidity: 78,
            wind_speed: 12,
            wind_dir: "उत्तर-पूर्व",
            aqi: 38
          },
          advisory: {
            text_bn: "আগামী ২-৩ দিন হালকা বৃষ্টি হতে পারে। জমিতে জল দাঁড়ানোর সুযোগ আছে। ধান গাছের ক্ষেতের নিকাশির ব্যবস্থা করুন। ইউরিয়া সার প্রয়োগ করুন।",
            text_en: "Light rain expected in next 2-3 days. Ensure proper drainage for paddy fields."
          },
          daily_forecast: [
            { day_bn: "আজ", day_en: "Today", date: "29 May", temp_max: 29, temp_min: 24, rain_prob: 40, rain_mm: "2-4 mm", icon: "⛅" },
            { day_bn: "শুক্র", day_en: "Fri", date: "30 May", temp_max: 30, temp_min: 24, rain_prob: 60, rain_mm: "5-8 mm", icon: "🌧️" },
            { day_bn: "শনিবার", day_en: "Sat", date: "31 May", temp_max: 30, temp_min: 25, rain_prob: 70, rain_mm: "8-12 mm", icon: "🌧️" },
            { day_bn: "রবি", day_en: "Sun", date: "01 Jun", temp_max: 31, temp_min: 25, rain_prob: 40, rain_mm: "2-4 mm", icon: "⛅" },
            { day_bn: "সোম", day_en: "Mon", date: "02 Jun", temp_max: 32, temp_min: 26, rain_prob: 20, rain_mm: "0-1 mm", icon: "⛅" }
          ]
        });
        setLoading(false);
      });
  }, [locationData]);

  // ==========================================
  // PAGE 1: LOCATION SELECTOR VIEW
  // ==========================================
  if (!locationData) {
    return (
      <div className="min-h-screen w-full relative flex flex-col justify-between overflow-x-hidden font-sans" style={{ background: 'linear-gradient(135deg, #e4f1ea 0%, #c1e2d1 100%)' }}>
        
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
          <div className="absolute top-12 left-12 flex items-center gap-3 opacity-80">
            <div className="text-5xl">☀️</div>
          </div>
          <div className="absolute bottom-0 inset-x-0 h-64 bg-repeat-x opacity-45 bg-bottom" style={{ backgroundImage: 'radial-gradient(circle, #2d6a4f 10px, transparent 11px)' }}></div>
        </div>

        <header className="w-full py-5 px-8 md:px-16 flex justify-between items-center relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center text-xl shadow">⛅</div>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight" style={{ color: '#163A32' }}>PanchMausam</h1>
              <p className="text-xs font-bold text-emerald-700">{t.tagline}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full text-sm font-bold border border-emerald-200 shadow-xs cursor-pointer">
              <select 
                value={lang} 
                onChange={(e) => setLang(e.target.value)}
                className="bg-transparent border-none outline-none font-bold text-slate-800 cursor-pointer"
              >
                <option value="en">English</option>
                <option value="bn">বাংলা</option>
                <option value="hi">हिंदी</option>
              </select>
            </div>
            <button className="text-sm font-bold text-slate-700 hover:text-emerald-900 transition cursor-pointer">
              {t.about}
            </button>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center p-4 relative z-10 my-auto">
          <LocationSelector onSelectLocation={handleSelectLocation} lang={lang} />
        </main>
      </div>
    );
  }

  // ==========================================
  // PAGES 2 & 3: DASHBOARD VIEW (Sidebar + Content)
  // ==========================================
  return (
    <div className="min-h-screen w-full flex flex-col bg-[#f4f7f5] text-[#082b20] font-sans">
      
      <header className="w-full bg-white border-b border-[#d7e2dc] py-3.5 px-6 md:px-10 flex justify-between items-center shadow-xs sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-600 rounded-full flex items-center justify-center text-lg shadow-xs text-white">⛅</div>
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-[#163A32]">PanchMausam</h1>
            <p className="text-[11px] font-bold text-emerald-700">{t.tagline}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-[#f4f7f5] border border-[#d7e2dc] px-3.5 py-2 rounded-full text-xs font-bold text-slate-800">
            <span>🌐</span>
            <select 
              value={lang} 
              onChange={(e) => setLang(e.target.value)}
              className="bg-transparent border-none outline-none font-bold cursor-pointer"
            >
              <option value="en">English</option>
              <option value="bn">বাংলা</option>
              <option value="hi">हिंदी</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-[#edf6ef] px-3.5 py-2 rounded-full text-xs font-bold border border-[#cfe0d4] text-[#1e5c3a]">
            <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
            <span>{t.online}</span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex flex-col md:flex-row p-6 gap-6 max-w-[1600px] w-full mx-auto">
        
        <aside className="w-full md:w-64 flex flex-col gap-4 shrink-0">
          <div className="bg-white border border-[#d7e2dc] rounded-3xl p-3 flex flex-col gap-1 shadow-xs">
            {[
              { id: 'home', label: t.home, icon: '🏠' },
              { id: 'forecast', label: t.forecast, icon: '📅' },
              { id: 'map', label: t.map, icon: '🗺️' },
              { id: 'advisory', label: t.advisory, icon: '🍃' },
              { id: 'more', label: t.more, icon: '⋯' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-3.5 px-4 py-3.5 rounded-2xl font-bold text-sm transition cursor-pointer ${
                  activeTab === item.id 
                    ? 'bg-[#e2f2e7] text-[#082b20] shadow-xs' 
                    : 'text-[#54786b] hover:bg-slate-50'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          <div className="bg-[#fff9e6] border border-[#f3e1a9] rounded-3xl p-4 text-xs">
            <div className="font-bold text-[#8c6d19] flex items-center gap-1.5 mb-1">
              <span>📶</span> {t.offlineMode}
            </div>
            <p className="text-[#736338] mb-2">{t.cachedData}</p>
            <p className="text-[11px] text-[#99844c]">{t.updated}: 8:30 AM</p>
          </div>

          <div className="bg-gradient-to-b from-emerald-100 to-emerald-200 border border-emerald-300 rounded-3xl p-4 flex flex-col items-center text-center overflow-hidden">
            <div className="text-3xl mb-2">🌾🏡</div>
            <p className="text-xs font-extrabold text-emerald-900 mb-1">{locationData.panchayat}</p>
            <p className="text-[10px] text-emerald-700 mb-3">{locationData.district}</p>
            <button 
              onClick={handleResetLocation} 
              className="text-xs font-bold bg-white text-emerald-900 px-3.5 py-2 rounded-xl shadow-xs hover:bg-emerald-50 transition cursor-pointer"
            >
              📍 {t.changeLocation}
            </button>
          </div>
        </aside>

        <main className="flex-1 flex flex-col gap-6">

          {activeTab === 'home' && forecast && !loading && (
            <div className="flex flex-col gap-6">
              
              <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center shadow-xs">
                <div>
                  <h2 className="text-2xl font-extrabold uppercase text-[#082b20]">
                    {locationData.panchayat || "AMDANGA"}, {locationData.block || "Amdanga Block"}
                  </h2>
                  <p className="text-xs font-bold text-[#54786b] mt-1">
                    {locationData.district || "North 24 Parganas"}, West Bengal
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-[#54786b] mt-3 sm:mt-0 bg-[#f4f7f5] px-4 py-2 rounded-xl">
                  <span>{t.updated}: 8:30 AM</span>
                  <span className="cursor-pointer">🔄</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div className="lg:col-span-7 bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col justify-between">
                  <p className="text-xs font-bold uppercase tracking-widest text-[#54786b] mb-4">{t.currentWeather}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                    <div className="sm:col-span-5 flex flex-col items-center sm:items-start text-center sm:text-left">
                      <div className="text-6xl mb-2">⛅</div>
                      <h3 className="text-2xl font-extrabold text-[#082b20]">
                        {lang === 'en' ? forecast.current?.condition_en : forecast.current?.condition_bn}
                      </h3>
                      <p className="text-xs text-[#54786b] mt-1">{t.feelsLike} {forecast.current?.feels_like}°C</p>
                    </div>
                    <div className="sm:col-span-7 grid grid-cols-2 gap-3 bg-[#f8faf9] p-4 rounded-2xl border border-[#e2e8e5]">
                      <div>
                        <span className="text-[11px] font-bold text-[#6a8479]">{t.temperature}</span>
                        <p className="text-lg font-extrabold text-[#082b20]">{forecast.current?.temp}°C</p>
                      </div>
                      <div>
                        <span className="text-[11px] font-bold text-[#6a8479]">{t.rainProb}</span>
                        <p className="text-lg font-extrabold text-[#082b20]">{forecast.current?.rain_prob}%</p>
                      </div>
                      <div className="pt-2 border-t border-[#e2e8e5]">
                        <span className="text-[11px] font-bold text-[#6a8479]">{t.rainfall}</span>
                        <p className="text-base font-extrabold text-[#082b20]">{forecast.current?.rain_mm} mm</p>
                      </div>
                      <div className="pt-2 border-t border-[#e2e8e5]">
                        <span className="text-[11px] font-bold text-[#6a8479]">{t.humidity}</span>
                        <p className="text-base font-extrabold text-[#082b20]">{forecast.current?.humidity}%</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-[#edf6ef] border border-[#cfe0d4] rounded-3xl p-6 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-xs font-extrabold uppercase tracking-widest text-[#1e5c3a]">🍃 {t.agroAdvisory}</span>
                      <span className="text-[10px] bg-[#dceee0] px-2.5 py-1 rounded-full font-bold text-[#1e5c3a]">{t.highPriority}</span>
                    </div>
                    <p className="text-xs sm:text-sm text-[#082b20] font-medium leading-relaxed">
                      {lang === 'en' ? forecast.advisory?.text_en : forecast.advisory?.text_bn}
                    </p>
                  </div>
                  <div className="mt-4 flex items-center justify-between bg-[#1e5c3a] text-white p-3 rounded-2xl shadow-xs">
                    <div className="flex items-center gap-2">
                      <span>🔊</span> <span className="text-xs font-bold">{t.listen}</span>
                    </div>
                    <span className="text-xs tracking-widest text-emerald-300">📶📶📶</span>
                  </div>
                </div>

              </div>

              <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-extrabold text-[#082b20] flex items-center gap-2">
                    <span>📅</span> {t.fiveDayForecast}
                  </h3>
                  <span onClick={() => setActiveTab('forecast')} className="text-xs font-bold text-emerald-700 cursor-pointer hover:underline">{t.viewDetails} →</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                  {forecast.daily_forecast?.map((day, idx) => (
                    <div key={idx} className="bg-[#f8faf9] border border-[#e2e8e5] p-3 rounded-2xl text-center">
                      <p className="text-xs font-extrabold text-emerald-850">
                        {lang === 'en' ? day.day_en : day.day_bn}
                      </p>
                      <p className="text-[10px] text-[#6a8479] mb-1">{day.date}</p>
                      <div className="text-2xl my-1">{day.icon}</div>
                      <p className="text-xs font-extrabold text-[#082b20]">{day.temp_max}°C / {day.temp_min}°C</p>
                      <p className="text-[10px] text-[#6a8479] mt-1">💧 {day.rain_prob}% ({day.rain_mm})</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-[#e8f4ed] border border-[#b8d6c3] p-4 rounded-2xl text-xs text-[#082b20] flex items-center gap-3">
                <span className="text-lg">ℹ️</span>
                <span>{t.rainAlert}</span>
              </div>

            </div>
          )}

          {/* =========================================
              FORECAST TAB VIEW (Integrates ForecastView)
             ========================================= */}
          {activeTab === 'forecast' && forecast && !loading && (
            <ForecastView 
              forecast={forecast}
              locationData={locationData}
              lang={lang}
              t={t}
              onReturnHome={() => setActiveTab('home')}
            />
          )}

          {/* =========================================
              ADVISORY TAB VIEW (Integrates AdvisoryView)
             ========================================= */}
          {activeTab === 'advisory' && (
            <AdvisoryView 
              forecast={forecast}
              locationData={locationData}
              lang={lang}
              t={t}
              onReturnHome={() => setActiveTab('home')}
            />
          )}

          {/* =========================================
              MAP COMPARISON VIEW
             ========================================= */}
          {activeTab === 'map' && (
            <div className="flex flex-col gap-6">
              
              <div className="bg-white border border-[#d7e2dc] rounded-3xl p-4 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 shadow-xs">
                <div>
                  <h2 className="text-xl font-extrabold text-[#082b20] flex items-center gap-2">
                    <span>🗺️</span> {t.forecastComparisonMap}
                  </h2>
                  <p className="text-xs text-[#54786b] mt-0.5">{t.mapSubtitle}</p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <div className="flex flex-col">
                    <span className="font-bold text-[#54786b] mb-1">{t.district}</span>
                    <select className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl font-bold">
                      <option>North 24 Parganas</option>
                    </select>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-bold text-[#54786b] mb-1">{t.block}</span>
                    <select className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl font-bold">
                      <option>Amdanga</option>
                    </select>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-bold text-[#54786b] mb-1">{t.panchayat}</span>
                    <select className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl font-bold">
                      <option>{t.allPanchayats}</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div className="lg:col-span-7 bg-white border border-[#d7e2dc] rounded-3xl p-5 shadow-xs flex flex-col justify-between">
                  <div className="bg-[#f8faf9] border border-[#e2e8e5] rounded-2xl p-3 flex justify-between items-center mb-4 text-xs font-bold">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center">🗺️</span>
                      <div>
                        <p className="text-[#082b20]">{t.blockLevelRef}</p>
                        <p className="text-[10px] text-[#54786b]">{t.referenceAvg}</p>
                      </div>
                    </div>
                    <div className="flex gap-3 text-[#082b20]">
                      <span>🌡️ <b>28°C</b></span>
                      <span>🌧️ <b>4.2 mm</b></span>
                      <span>💧 <b>72%</b></span>
                    </div>
                  </div>

                  <div className="relative w-full h-[360px] bg-emerald-100/50 rounded-2xl border border-emerald-200 flex items-center justify-center overflow-hidden">
                    <div className="grid grid-cols-3 gap-3 text-center text-xs font-extrabold w-full max-w-md p-4">
                      <div className="p-3 bg-emerald-400 text-emerald-950 rounded-xl shadow-xs">Barasat</div>
                      <div className="p-3 bg-amber-300 text-amber-950 rounded-xl shadow-xs">Kalyanpur</div>
                      <div className="p-3 bg-emerald-300 text-emerald-950 rounded-xl shadow-xs">Rajarhat</div>
                      <div className="p-3 bg-emerald-400 text-emerald-950 rounded-xl shadow-xs">Chanditala</div>
                      <div className="p-3 bg-amber-400 text-amber-950 rounded-xl border-2 border-white shadow-md scale-105">
                        <span className="text-[9px] bg-white px-1 rounded text-slate-900 block mb-0.5">AMDANGA</span>
                        Amdanga
                      </div>
                      <div className="p-3 bg-orange-400 text-orange-950 rounded-xl shadow-xs">Haripur</div>
                      <div className="p-3 bg-emerald-400 text-emerald-950 rounded-xl shadow-xs">Madhyamgram</div>
                      <div className="p-3 bg-emerald-400 text-emerald-950 rounded-xl shadow-xs">Bamangachi</div>
                    </div>
                    <div className="absolute bottom-3 left-3 bg-white px-2.5 py-1 rounded-lg text-[10px] font-bold shadow-xs">Leaflet</div>
                  </div>
                  <div className="mt-3 p-2 bg-sky-50 text-sky-900 text-xs rounded-xl">
                    ℹ️ {t.mapNotice}
                  </div>
                </div>

                <div className="lg:col-span-5 flex flex-col gap-4">
                  <div className="bg-white border border-[#d7e2dc] rounded-3xl p-5 shadow-xs">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full">{t.panchayatLevel}</span>
                        <h3 className="text-xl font-extrabold text-[#082b20] mt-1">AMDANGA</h3>
                        <p className="text-xs text-[#54786b]">Amdanga Block, North 24 Parganas</p>
                      </div>
                      <span className="cursor-pointer text-slate-400 hover:text-slate-700">✕</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 bg-[#f8faf9] p-3 rounded-2xl mb-4 text-xs">
                      <div>
                        <span className="text-[#54786b] font-bold">{t.rainfall}</span>
                        <p className="text-sm font-extrabold text-[#082b20]">2.4 mm</p>
                      </div>
                      <div>
                        <span className="text-[#54786b] font-bold">{t.rainProb} / {t.humidity}</span>
                        <p className="text-sm font-extrabold text-[#082b20]">32°C / 75%</p>
                      </div>
                    </div>

                    <div className="bg-[#edf6ef] p-3.5 rounded-2xl border border-[#cfe0d4]">
                      <span className="text-xs font-bold text-[#1e5c3a] block mb-1">🍃 {t.agroAdvisory}</span>
                      <p className="text-xs text-[#082b20] leading-relaxed">
                        {lang === 'en' ? forecast?.advisory?.text_en : forecast?.advisory?.text_bn}
                      </p>
                    </div>
                  </div>

                  <div className="bg-white border border-[#d7e2dc] rounded-3xl p-5 shadow-xs">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#54786b] mb-3">{t.forecastRiskLevel}</h4>
                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-2 bg-emerald-50 border border-emerald-200 rounded-xl">
                        <div className="w-3 h-3 bg-emerald-500 rounded-full mx-auto mb-1"></div>
                        <span className="font-bold text-emerald-900">{t.low}</span>
                        <p className="text-[9px] text-slate-500">0-5 mm</p>
                      </div>
                      <div className="p-2 bg-amber-50 border border-amber-200 rounded-xl">
                        <div className="w-3 h-3 bg-amber-400 rounded-full mx-auto mb-1"></div>
                        <span className="font-bold text-amber-900">{t.moderate}</span>
                        <p className="text-[9px] text-slate-500">6-15 mm</p>
                      </div>
                      <div className="p-2 bg-orange-50 border border-orange-200 rounded-xl">
                        <div className="w-3 h-3 bg-orange-500 rounded-full mx-auto mb-1"></div>
                        <span className="font-bold text-orange-900">{t.high}</span>
                        <p className="text-[9px] text-slate-500">16-30 mm</p>
                      </div>
                      <div className="p-2 bg-purple-50 border border-purple-200 rounded-xl">
                        <div className="w-3 h-3 bg-purple-500 rounded-full mx-auto mb-1"></div>
                        <span className="font-bold text-purple-900">{t.veryHigh}</span>
                        <p className="text-[9px] text-slate-500">&gt;30 mm</p>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {activeTab !== 'home' && activeTab !== 'forecast' && activeTab !== 'advisory' && activeTab !== 'map' && (
            <div className="bg-white border border-[#d7e2dc] rounded-3xl p-8 text-center shadow-xs">
              <h2 className="text-xl font-extrabold text-[#082b20] mb-2 capitalize">{activeTab} {t.viewSection}</h2>
              <button 
                onClick={() => setActiveTab('home')}
                className="px-6 py-2 bg-emerald-600 text-white rounded-xl font-bold shadow-xs cursor-pointer mt-4"
              >
                {t.returnHome}
              </button>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}