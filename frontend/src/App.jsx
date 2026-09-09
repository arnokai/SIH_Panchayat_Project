// src/App.jsx
import React, { useState } from 'react';
import './App.css';

export default function App() {
  const [locationData, setLocationData] = useState(() => {
    const saved = localStorage.getItem('panchmausam_loc');
    return saved ? JSON.parse(saved) : null;
  });

  const [activeTab, setActiveTab] = useState('home');
  const [lang, setLang] = useState('bn'); // 'en', 'bn', 'hi'

  // Dropdown states for Landing Page
  const [selectedDistrict, setSelectedDistrict] = useState('North 24 Parganas');
  const [selectedBlock, setSelectedBlock] = useState('Amdanga');
  const [selectedPanchayat, setSelectedPanchayat] = useState('AMDANGA');

  const handleViewForecast = () => {
    const locInfo = {
      district: selectedDistrict,
      block: selectedBlock,
      panchayat: selectedPanchayat,
      panchayat_id: "107778"
    };
    setLocationData(locInfo);
    localStorage.setItem('panchmausam_loc', JSON.stringify(locInfo));
  };

  const handleResetLocation = () => {
    localStorage.removeItem('panchmausam_loc');
    setLocationData(null);
  };

  // Multilingual Dictionaries matching your designs
  const t = {
    en: {
      brand: "PanchMausam",
      tagline: "Smarter Weather, Better Farming",
      selectTitle: "Select Your Location",
      selectSubtitle: "Get accurate weather and advisory for your Panchayat",
      district: "District",
      block: "Block",
      panchayat: "Panchayat",
      useCurrent: "Use My Current Location",
      viewForecastBtn: "VIEW FORECAST",
      home: "Home",
      forecast: "Forecast",
      map: "Map",
      advisory: "Advisory",
      more: "More",
      offlineMode: "Offline Mode",
      cachedNotice: "Showing cached data",
      updatedTime: "Last updated: Today, 8:30 AM",
      currentWeather: "Current Weather",
      temp: "Temperature",
      feelsLike: "Feels like",
      rainProb: "Rain Prob.",
      rainfall: "Rainfall",
      humidity: "Humidity",
      windSpeed: "Wind Speed",
      airQuality: "Air Quality",
      agroAdvisory: "Agro Advisory",
      listen: "Listen (Voice)",
      extraTip: "Tip: Clear weeds if water stagnation occurs.",
      fiveDay: "5-Day Forecast",
      viewDetails: "View Details",
      rainAlertBanner: "Light to moderate rain is expected in your area. Keep an umbrella when going outside.",
      mapTitle: "Forecast Comparison Map",
      mapSubtitle: "See how the forecast varies across Panchayats within a Block.",
      riskLow: "Low",
      riskMod: "Moderate",
      riskHigh: "High",
      riskVHigh: "Very High",
      officerDashboard: "Officer & Admin Review Dashboard",
      officerNotice: "This is a high-risk weather alert zone requiring official agriculture department review."
    },
    bn: {
      brand: "PanchMausam",
      tagline: "স্মার্ট আবহাওয়া, উন্নত কৃষি",
      selectTitle: "আপনার অবস্থান নির্বাচন করুন",
      selectSubtitle: "আপনার পঞ্চায়েতের জন্য সঠিক আবহাওয়া ও কৃষি পরামর্শ পান",
      district: "জেলা",
      block: "ব্লক",
      panchayat: "পঞ্চায়েত",
      useCurrent: "আমার বর্তমান অবস্থান ব্যবহার করুন",
      viewForecastBtn: "পূর্বাভাস দেখুন",
      home: "হোম",
      forecast: "পূর্বাভাস",
      map: "ম্যাপ",
      advisory: "পরামর্শ",
      more: "আরও",
      offlineMode: "অফলাইন মোড",
      cachedNotice: "ক্যাশে থাকা তথ্য দেখানো হচ্ছে",
      updatedTime: "আপডেট: আজ, সকাল ৮:৩০",
      currentWeather: "এখনকার আবহাওয়া",
      temp: "তাপমাত্রা",
      feelsLike: "অনুভূত",
      rainProb: "বৃষ্টি সম্ভাবনা",
      rainfall: "বৃষ্টিপাত",
      humidity: "আর্দ্রতা",
      windSpeed: "বাতাসের গতি",
      airQuality: "বায়ুর গুণমান",
      agroAdvisory: "কৃষি পরামর্শ",
      listen: "শুনুন (Listen)",
      extraTip: "পরামর্শ: জমিতে জল জমে থাকলে আগাছা পরিষ্কার করুন।",
      fiveDay: "৫ দিনের পূর্বাভাস",
      viewDetails: "বিস্তারিত দেখুন",
      rainAlertBanner: "আপনার এলাকায় হালকা থেকে মাঝারি বৃষ্টির সম্ভাবনা রয়েছে। বাইরে যাওয়ার সময় ছাতা সাথে রাখুন।",
      mapTitle: "পূর্বাভাস তুলনা মানচিত্র",
      mapSubtitle: "একটি ব্লকের অধীনে বিভিন্ন পঞ্চায়েতের আবহাওয়ার পূর্বাভাস কীভাবে পরিবর্তিত হয় তা দেখুন।",
      riskLow: "কম",
      riskMod: "মাঝারি",
      riskHigh: "বেশি",
      riskVHigh: "খুব বেশি",
      officerDashboard: "অফিসিয়াল পর্যালোচনা ড্যাশবোর্ড",
      officerNotice: "এটি একটি উচ্চ ঝুঁকির আবহাওয়া সতর্কতা। কত্ক/কৃষি দপ্তরের অফিসিয়াল পর্যালোচনা প্রয়োজন।"
    },
    hi: {
      brand: "PanchMausam",
      tagline: "बेहतर मौसम, उन्नत खेती",
      selectTitle: "अपना स्थान चुनें",
      selectSubtitle: "अपनी पंचायत के लिए सटीक मौसम और कृषि सलाह प्राप्त करें",
      district: "जिला",
      block: "ब्लॉक",
      panchayat: "पंचायत",
      useCurrent: "मेरा वर्तमान स्थान उपयोग करें",
      viewForecastBtn: "पूर्वानुमान देखें",
      home: "होम",
      forecast: "पूर्वानुमान",
      map: "नक्शा",
      advisory: "सलाह",
      more: "और अधिक",
      offlineMode: "ऑफ़लाइन मोड",
      cachedNotice: "कैश्ड डेटा दिखाया जा रहा है",
      updatedTime: "अपडेट: आज, सुबह 8:30",
      currentWeather: "वर्तमान मौसम",
      temp: "तापमान",
      feelsLike: "महसूस होता है",
      rainProb: "बारिश की संभावना",
      rainfall: "वर्षा",
      humidity: "आर्द्रता",
      windSpeed: "हवा की गति",
      airQuality: "वायु गुणवत्ता",
      agroAdvisory: "कृषि सलाह",
      listen: "सुनें (Listen)",
      extraTip: "सलाह: खेत में पानी जमा होने पर खरपतवार हटाएं।",
      fiveDay: "5-दिन का पूर्वानुमान",
      viewDetails: "विस्तृत देखें",
      rainAlertBanner: "आपके क्षेत्र में हल्की से मध्यम बारिश की संभावना है। बाहर जाते समय छाता साथ रखें।",
      mapTitle: "पूर्वानुमान तुलना नक्शा",
      mapSubtitle: "देखें कि एक ब्लॉक के भीतर विभिन्न पंचायतों में पूर्वानुमान कैसे भिन्न होता है।",
      riskLow: "कम",
      riskMod: "मध्यम",
      riskHigh: "अधिक",
      riskVHigh: "बहुत अधिक",
      officerDashboard: "अधिकारी और प्रशासनिक समीक्षा डैशबोर्ड",
      officerNotice: "यह उच्च जोखिम वाला मौसम अलर्ट है, कृषि विभाग की समीक्षा आवश्यक है।"
    }
  }[lang];

  // SCREEN 1: LANDING & LOCATION SELECTOR (Matches Image 1)
  if (!locationData) {
    return (
      <div className="min-h-screen w-full relative flex flex-col justify-between overflow-x-hidden font-sans bg-gradient-to-br from-[#e4f1ea] to-[#c1e2d1]">
        {/* Header */}
        <header className="w-full py-6 px-10 md:px-16 flex justify-between items-center relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center text-xl shadow">⛅</div>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-[#163A32]">{t.brand}</h1>
              <p className="text-xs font-bold text-emerald-700">{t.tagline}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <select 
              value={lang} 
              onChange={(e) => setLang(e.target.value)}
              className="bg-white/90 px-4 py-2 rounded-full text-sm font-bold border border-emerald-300 outline-none cursor-pointer shadow-xs"
            >
              <option value="en">English</option>
              <option value="bn">বাংলা</option>
              <option value="hi">हिंदी</option>
            </select>
            <span className="text-sm font-bold text-emerald-900 cursor-pointer">About</span>
          </div>
        </header>

        {/* Center Card Container */}
        <main className="flex-1 flex items-center justify-center p-4 relative z-10">
          <div className="bg-white/85 backdrop-blur-md border border-white/60 rounded-3xl p-8 max-w-lg w-full shadow-2xl flex flex-col gap-6">
            <div>
              <h2 className="text-2xl font-extrabold text-[#082b20]">{t.selectTitle}</h2>
              <p className="text-xs font-bold text-[#54786b] mt-1">{t.selectSubtitle}</p>
            </div>

            <div className="flex flex-col gap-4">
              <div>
                <label className="text-xs font-bold text-[#082b20] mb-1 block">{t.district}</label>
                <select 
                  value={selectedDistrict}
                  onChange={(e) => setSelectedDistrict(e.target.value)}
                  className="w-full bg-[#f4f7f5] border border-[#d7e2dc] p-3 rounded-xl font-bold text-sm outline-none"
                >
                  <option value="North 24 Parganas">North 24 Parganas</option>
                  <option value="Nadia">Nadia</option>
                  <option value="Hooghly">Hooghly</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-[#082b20] mb-1 block">{t.block}</label>
                <select 
                  value={selectedBlock}
                  onChange={(e) => setSelectedBlock(e.target.value)}
                  className="w-full bg-[#f4f7f5] border border-[#d7e2dc] p-3 rounded-xl font-bold text-sm outline-none"
                >
                  <option value="Amdanga">Amdanga</option>
                  <option value="Barasat I">Barasat I</option>
                  <option value="Habra I">Habra I</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-[#082b20] mb-1 block">{t.panchayat}</label>
                <select 
                  value={selectedPanchayat}
                  onChange={(e) => setSelectedPanchayat(e.target.value)}
                  className="w-full bg-[#f4f7f5] border border-[#d7e2dc] p-3 rounded-xl font-bold text-sm outline-none"
                >
                  <option value="AMDANGA">AMDANGA</option>
                  <option value="Haripur">Haripur</option>
                  <option value="Kalyanpur">Kalyanpur</option>
                  <option value="Chanditala">Chanditala</option>
                </select>
              </div>
            </div>

            <button className="text-xs font-bold text-emerald-800 flex items-center gap-2 hover:underline cursor-pointer">
              <span>📍</span> {t.useCurrent}
            </button>

            <button 
              onClick={handleViewForecast}
              className="w-full py-4 bg-[#0095ff] hover:bg-[#0080e6] text-white font-extrabold rounded-2xl shadow-lg transition flex items-center justify-center gap-2 cursor-pointer text-sm tracking-wider"
            >
              <span>{t.viewForecastBtn}</span>
              <span>→</span>
            </button>
          </div>
        </main>
      </div>
    );
  }

  // SCREEN 2: MAIN DASHBOARD (Matches Images 2, 3, and 4)
  return (
    <div className="min-h-screen w-full flex flex-col bg-[#f4f7f5] text-[#082b20] font-sans">
      {/* Top Header */}
      <header className="w-full bg-white border-b border-[#d7e2dc] py-3.5 px-6 md:px-10 flex justify-between items-center shadow-xs sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-600 rounded-full flex items-center justify-center text-lg text-white shadow">⛅</div>
          <div>
            <h1 className="text-xl font-extrabold text-[#163A32]">{t.brand}</h1>
            <p className="text-[11px] font-bold text-emerald-700">{t.tagline}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <select 
            value={lang} 
            onChange={(e) => setLang(e.target.value)}
            className="bg-[#f4f7f5] border border-[#d7e2dc] px-3.5 py-2 rounded-full text-xs font-bold cursor-pointer outline-none"
          >
            <option value="en">English</option>
            <option value="bn">বাংলা</option>
            <option value="hi">हिंदी</option>
          </select>
          <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full text-xs font-bold text-emerald-800">
            <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
            <span>{t.online} Online</span>
          </div>
        </div>
      </header>

      {/* App Body Container */}
      <div className="flex-1 flex flex-col md:flex-row p-6 gap-6 max-w-[1600px] w-full mx-auto">
        
        {/* Sidebar Navigation */}
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
                  activeTab === item.id ? 'bg-[#e2f2e7] text-[#082b20]' : 'text-[#54786b] hover:bg-slate-50'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          {/* Offline Box */}
          <div className="bg-[#fff9e6] border border-[#ffe099] rounded-3xl p-4 flex flex-col gap-2 shadow-xs">
            <div className="flex items-center gap-2 text-amber-800 font-extrabold text-xs">
              <span>⚡</span> {t.offlineMode}
            </div>
            <p className="text-[11px] font-bold text-amber-900">{t.cachedNotice}</p>
            <p className="text-[10px] text-amber-700 font-medium">{t.updatedTime}</p>
          </div>

          {/* Mini Village Art Box */}
          <div className="bg-gradient-to-t from-emerald-200 to-emerald-100 rounded-3xl p-4 h-40 flex items-end justify-center border border-emerald-300 shadow-xs relative overflow-hidden">
            <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:16px_16px]"></div>
            <span className="text-xs font-extrabold text-emerald-900 z-10 bg-white/80 px-3 py-1 rounded-full shadow-xs">
              {locationData.panchayat} Village View
            </span>
          </div>

          <button 
            onClick={handleResetLocation} 
            className="text-xs font-bold bg-emerald-100 hover:bg-emerald-200 text-emerald-900 p-3 rounded-2xl shadow-xs transition cursor-pointer text-center"
          >
            📍 Change Panchayat Location
          </button>
        </aside>

        {/* Dynamic Main Content Window based on active tab */}
        <main className="flex-1 flex flex-col gap-6">
          
          {/* TAB 1: HOME (Matches Image 2) */}
          {activeTab === 'home' && (
            <>
              {/* Top Banner Bar */}
              <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-600 text-xl">📍</span>
                    <h2 className="text-2xl font-extrabold uppercase text-[#082b20]">
                      {locationData.panchayat}, {locationData.block} Block
                    </h2>
                  </div>
                  <p className="text-xs font-bold text-[#54786b] mt-0.5">{locationData.district}, West Bengal</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs font-bold text-[#54786b]">{t.updatedTime}</span>
                  <button onClick={() => window.location.reload()} className="p-2 bg-emerald-50 rounded-full hover:bg-emerald-100 cursor-pointer">🔄</button>
                </div>
              </div>

              {/* Weather & Advisory Split Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Weather Card */}
                <div className="lg:col-span-7 bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col justify-between">
                  <h3 className="text-xs font-extrabold text-[#54786b] uppercase tracking-wider mb-4">{t.currentWeather}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                    <div className="md:col-span-5 flex flex-col items-center justify-center p-4 bg-emerald-50/50 rounded-2xl border border-emerald-100">
                      <span className="text-6xl mb-2">⛅</span>
                      <h4 className="text-xl font-extrabold text-[#082b20]">Partly Cloudy</h4>
                      <p className="text-xs font-bold text-[#54786b] mt-1">{t.feelsLike}: 31°C</p>
                    </div>
                    <div className="md:col-span-7 grid grid-cols-2 gap-3">
                      <div className="bg-[#f4f7f5] p-3.5 rounded-2xl border border-[#d7e2dc]">
                        <span className="text-xs font-bold text-[#54786b]">{t.temp}</span>
                        <p className="text-xl font-extrabold text-[#082b20] mt-1">28°C</p>
                        <span className="text-[10px] text-emerald-700 font-bold">{t.feelsLike} 31°C</span>
                      </div>
                      <div className="bg-[#f4f7f5] p-3.5 rounded-2xl border border-[#d7e2dc]">
                        <span className="text-xs font-bold text-[#54786b]">{t.rainProb}</span>
                        <p className="text-xl font-extrabold text-[#082b20] mt-1">40%</p>
                        <span className="text-[10px] text-emerald-700 font-bold">Moderate</span>
                      </div>
                      <div className="bg-[#f4f7f5] p-3.5 rounded-2xl border border-[#d7e2dc]">
                        <span className="text-xs font-bold text-[#54786b]">{t.rainfall}</span>
                        <p className="text-xl font-extrabold text-[#082b20] mt-1">2.4 mm</p>
                        <span className="text-[10px] text-[#54786b]">Past 24 hrs</span>
                      </div>
                      <div className="bg-[#f4f7f5] p-3.5 rounded-2xl border border-[#d7e2dc]">
                        <span className="text-xs font-bold text-[#54786b]">{t.humidity}</span>
                        <p className="text-xl font-extrabold text-[#082b20] mt-1">78%</p>
                        <span className="text-[10px] text-emerald-700 font-bold">Humid</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Advisory Card */}
                <div className="lg:col-span-5 bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col justify-between bg-gradient-to-br from-white to-emerald-50/40">
                  <div>
                    <div className="flex items-center gap-2 text-emerald-700 font-extrabold text-xs mb-3">
                      <span>🍃</span> {t.agroAdvisory}
                    </div>
                    <p className="text-sm font-bold text-[#082b20] leading-relaxed">
                      Light rain expected in next 2-3 days. Ensure proper drainage for paddy fields. Apply fertilizer after rain stops.
                    </p>
                  </div>
                  <div className="mt-6 flex flex-col gap-3">
                    <button className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-2xl shadow-sm text-xs flex items-center justify-center gap-2 cursor-pointer transition">
                      <span>🔊</span> {t.listen}
                    </button>
                    <div className="bg-[#fff9e6] border border-[#ffe099] p-2.5 rounded-xl text-xs font-bold text-amber-900 flex items-center gap-2">
                      <span>💡</span> {t.extraTip}
                    </div>
                  </div>
                </div>
              </div>

              {/* 5-Day Forecast Row */}
              <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-extrabold uppercase text-[#082b20] tracking-wider">{t.fiveDay}</h3>
                  <button onClick={() => setActiveTab('forecast')} className="text-xs font-extrabold text-emerald-700 hover:underline cursor-pointer">{t.viewDetails} →</button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                  {[
                    { day: 'Today', date: '29 May', icon: '⛅', max: 29, min: 24, rain: '40%' },
                    { day: 'Fri', date: '30 May', icon: '🌧️', max: 30, min: 24, rain: '60%' },
                    { day: 'Sat', date: '31 May', icon: '🌧️', max: 30, min: 25, rain: '70%' },
                    { day: 'Sun', date: '01 Jun', icon: '⛅', max: 31, min: 25, rain: '40%' },
                    { day: 'Mon', date: '02 Jun', icon: '☀️', max: 32, min: 26, rain: '20%' },
                  ].map((d, i) => (
                    <div key={i} className="bg-[#f4f7f5] border border-[#d7e2dc] rounded-2xl p-4 flex flex-col items-center text-center">
                      <span className="text-xs font-bold text-emerald-800">{d.day}</span>
                      <span className="text-[11px] text-[#54786b] mb-2">{d.date}</span>
                      <span className="text-3xl my-1">{d.icon}</span>
                      <span className="text-sm font-extrabold text-[#082b20] mt-1">{d.max}°C / {d.min}°C</span>
                      <span className="text-[11px] font-bold text-blue-600 mt-1">💧 {d.rain}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Notice Bar */}
              <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 text-xs font-bold text-blue-900 flex items-center gap-3">
                <span className="text-lg">ℹ️</span>
                <span>{t.rainAlertBanner}</span>
              </div>
            </>
          )}

          {/* TAB 2: FORECAST (Matches Image 3 Detail View) */}
          {activeTab === 'forecast' && (
            <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col gap-6">
              <div className="flex justify-between items-center border-b border-[#d7e2dc] pb-4">
                <div>
                  <h2 className="text-xl font-extrabold text-[#082b20]">Detailed Weather & Forecast Suite</h2>
                  <p className="text-xs font-bold text-[#54786b]">Comprehensive meteorological breakdown for {locationData.panchayat}</p>
                </div>
                <button onClick={() => setActiveTab('home')} className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold">Back to Home</button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-emerald-50 border border-emerald-200 p-5 rounded-2xl">
                  <h4 className="text-xs font-extrabold text-emerald-800 uppercase">Hourly Trend</h4>
                  <p className="text-2xl font-extrabold text-[#082b20] mt-2">Stable (28°C)</p>
                  <p className="text-xs text-emerald-700 mt-1">No sudden wind gusts expected until evening.</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 p-5 rounded-2xl">
                  <h4 className="text-xs font-extrabold text-blue-800 uppercase">Precipitation Accumulation</h4>
                  <p className="text-2xl font-extrabold text-[#082b20] mt-2">12.4 mm</p>
                  <p className="text-xs text-blue-700 mt-1">Expected over the next 48 hours.</p>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-5 rounded-2xl">
                  <h4 className="text-xs font-extrabold text-amber-800 uppercase">Soil Moisture Status</h4>
                  <p className="text-2xl font-extrabold text-[#082b20] mt-2">Optimal (74%)</p>
                  <p className="text-xs text-amber-700 mt-1">Good condition for vegetative crop stage.</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: MAP (Matches Image 4) */}
          {activeTab === 'map' && (
            <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col gap-6">
              <div>
                <h2 className="text-2xl font-extrabold text-[#082b20]">{t.mapTitle}</h2>
                <p className="text-xs font-bold text-[#54786b]">{t.mapSubtitle}</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-8 bg-[#e4f1ea] border border-[#d7e2dc] rounded-3xl h-[400px] flex items-center justify-center relative overflow-hidden shadow-inner">
                  <div className="absolute inset-0 bg-emerald-200/40 flex flex-col items-center justify-center gap-3">
                    <span className="text-4xl">🗺️</span>
                    <p className="text-sm font-extrabold text-emerald-900">Interactive Panchayat Risk Heatmap Active</p>
                    <div className="flex gap-2">
                      <span className="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-bold">Barasat (Low)</span>
                      <span className="px-3 py-1 bg-yellow-400 text-slate-900 rounded-full text-xs font-bold">{locationData.panchayat} (Moderate)</span>
                      <span className="px-3 py-1 bg-orange-500 text-white rounded-full text-xs font-bold">Haripur (High)</span>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-4 flex flex-col gap-4">
                  <div className="bg-[#f4f7f5] border border-[#d7e2dc] rounded-3xl p-5 flex flex-col gap-3">
                    <h4 className="text-xs font-extrabold uppercase text-[#082b20]">Risk Level Index</h4>
                    <div className="flex items-center gap-3"><span className="w-4 h-4 rounded-full bg-green-500"></span><span className="text-xs font-bold">{t.riskLow} (0-5 mm)</span></div>
                    <div className="flex items-center gap-3"><span className="w-4 h-4 rounded-full bg-yellow-400"></span><span className="text-xs font-bold">{t.riskMod} (6-15 mm)</span></div>
                    <div className="flex items-center gap-3"><span className="w-4 h-4 rounded-full bg-orange-500"></span><span className="text-xs font-bold">{t.riskHigh} (16-30 mm)</span></div>
                    <div className="flex items-center gap-3"><span className="w-4 h-4 rounded-full bg-purple-600"></span><span className="text-xs font-bold">{t.riskVHigh} (&gt;30 mm)</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ADVISORY */}
          {activeTab === 'advisory' && (
            <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col gap-6">
              <h2 className="text-2xl font-extrabold text-[#082b20]">{t.agroAdvisory} Dashboard</h2>
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl">
                <h4 className="text-lg font-extrabold text-emerald-900 mb-2">Paddy Crop Advisory (Vegetative Stage)</h4>
                <p className="text-sm font-bold text-[#082b20] leading-relaxed">
                  Due to high humidity and expected rainfall, farmers are advised to avoid heavy nitrogen fertilizer application. Keep field drainage channels open to prevent root rot.
                </p>
              </div>
            </div>
          )}

          {/* TAB 5: MORE (Officer Dashboard) */}
          {activeTab === 'more' && (
            <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col gap-6">
              <h2 className="text-2xl font-extrabold text-[#082b20]">{t.officerDashboard}</h2>
              <div className="p-5 bg-amber-50 border border-amber-200 rounded-2xl flex flex-col gap-3">
                <span className="text-xs font-extrabold uppercase text-amber-900">🔒 Restricted Admin View</span>
                <p className="text-sm font-bold text-amber-950">{t.officerNotice}</p>
                <button className="self-start px-5 py-2.5 bg-amber-600 text-white rounded-xl text-xs font-extrabold shadow">Approve Block Bulletin</button>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}