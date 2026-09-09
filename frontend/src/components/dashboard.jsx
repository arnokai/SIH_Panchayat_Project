// src/components/Dashboard.jsx
import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix for default marker icons in React-Leaflet
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

export default function Dashboard({ locationData, onBackToSelector }) {
  const [lang, setLang] = useState('bn'); // Default to Bengali

  // Multi-language dictionary mapped to your design
  const t = {
    en: {
      brand: "PanchMausam",
      tagline: "Smarter Weather, Better Farming",
      back: "Back",
      lastUpdated: "Last updated: Today, 8:30 AM",
      recHeader: "RECOMMENDED ACTION FOR TODAY",
      advisoryText: "Provide light irrigation and do not allow excess water to accumulate in the field.",
      advisoryNote: "There is a chance of moderate rain today, and high soil moisture means excess water can damage crops.",
      cropLabel: "Crop",
      cropVal: "Rice (धान)",
      stageLabel: "Crop Stage",
      stageVal: "Vegetative Stage",
      sourceLabel: "Source",
      sourceVal: "KVK, North 24 Parganas",
      currentWeatherHeader: "Current Weather",
      rainProb: "Rain Probability",
      windSpeed: "Wind Speed",
      humidity: "Humidity",
      tempRange: "Temperature",
      fiveDayHeader: "5-Day Forecast",
      neighborStatus: "Neighboring Panchayat Status Map",
      viewOnMap: "Expanded View",
      offlineNotice: "Showing in Offline Mode"
    },
    bn: {
      brand: "PanchMausam",
      tagline: "স্মার্ট আবহাওয়া, উন্নত চাষবাস",
      back: "পেছনে",
      lastUpdated: "Last updated: আজ, 8:30 AM",
      recHeader: "আজকের জন্য সুপারিশকৃত পদক্ষেপ",
      advisoryText: "হালকা সেচ দিন এবং জমিতে অতিরিক্ত জল জমতে দেবেন না।",
      advisoryNote: "আজ মাঝারি বৃষ্টির সম্ভাবনা রয়েছে এবং মাটিতে আর্দ্রতা বেশি থাকায় অতিরিক্ত জল জমলে ফসলের ক্ষতি হতে পারে।",
      cropLabel: "ফসল",
      cropVal: "ধান (Rice)",
      stageLabel: "ফসলের পর্যায়",
      stageVal: "বৃদ্ধি পর্যায়",
      sourceLabel: "উৎস",
      sourceVal: "কৃষি বিজ্ঞান কেন্দ্র, উত্তর ২৪ পরগনা",
      currentWeatherHeader: "আজকের আবহাওয়া",
      rainProb: "বৃষ্টির সম্ভাবনা",
      windSpeed: "বাতাসের গতি",
      humidity: "আর্দ্রতা",
      tempRange: "তাপমাত্রা",
      fiveDayHeader: "৫ দিনের পূর্বাভাস",
      neighborStatus: "পাশের পঞ্চায়েতের অবস্থা মানচিত্র",
      viewOnMap: "বড় মানচিত্র",
      offlineNotice: "অফলাইন মোডে দেখানো হচ্ছে"
    },
    hi: {
      brand: "PanchMausam",
      tagline: "बेहतर मौसम, बेहतर खेती",
      back: "पीछे",
      lastUpdated: "अंतिम अपडेट: आज, 8:30 AM",
      recHeader: "आज के लिए अनुशंसित कार्रवाई",
      advisoryText: "हल्का सिंचाई दें और खेत में अत्यधिक पानी जमा न होने दें।",
      advisoryNote: "आज मध्यम बारिश की संभावना है और अधिक नमी के कारण फसल को नुकसान हो सकता है।",
      cropLabel: "फसल",
      cropVal: "धान (Rice)",
      stageLabel: "फसल चरण",
      stageVal: "वानस्पतिक चरण",
      sourceLabel: "स्रोत",
      sourceVal: "कृषि विज्ञान केंद्र, उत्तर 24 परगना",
      currentWeatherHeader: "आज का मौसम",
      rainProb: "बारिश की संभावना",
      windSpeed: "हवा की गति",
      humidity: "नमी",
      tempRange: "तापमान",
      fiveDayHeader: "5-दिवसीय पूर्वानुमान",
      neighborStatus: "आसपास की पंचायत की स्थिति मानचित्र",
      viewOnMap: "विस्तृत मानचित्र",
      offlineNotice: "ऑफ़लाइन मोड में दिखाया जा रहा है"
    }
  };

  const tVal = t[lang] || t.bn;
  const loc = locationData || { district: "North 24 Parganas", block: "Amdanga", panchayat: "AMDANGA" };

  // Map coordinates configuration
  const centerPosition = [22.8465, 88.5534];
  const locations = [
    { name: "Amdanga (Selected)", pos: [22.8465, 88.5534], risk: "Moderate" },
    { name: "Barasat", pos: [22.7211, 88.4811], risk: "Safe" },
    { name: "Kalyanpur", pos: [22.8800, 88.5200], risk: "Moderate" },
    { name: "Haripur", pos: [22.8200, 88.6000], risk: "High Risk" },
    { name: "Madhyamgram", pos: [22.7037, 88.4687], risk: "Safe" }
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="brand-block">
            <h1>{tVal.brand}</h1>
            <p>{tVal.tagline}</p>
          </div>
          <div>
            <select 
              value={lang} 
              onChange={(e) => setLang(e.target.value)}
              style={{ background: '#06372b', color: 'white', border: '1px solid #145c48', padding: '10px 18px', borderRadius: '14px', cursor: 'pointer', fontWeight: 'bold' }}
            >
              <option value="en">English</option>
              <option value="bn">বাংলা</option>
              <option value="hi">हिंदी</option>
            </select>
          </div>
        </div>
      </header>

      {/* Location Selector Bar */}
      <div style={{ background: 'white', borderBottom: '1px solid #d7e2dc', padding: '16px 0' }}>
        <div className="header-inner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <button 
              onClick={onBackToSelector}
              style={{ background: 'none', border: 'none', fontWeight: 'bold', cursor: 'pointer', color: '#082b20', fontSize: '15px' }}
            >
              ← {tVal.back}
            </button>
            <div className="location" style={{ margin: 0 }}>
              <span>📍</span> {loc.panchayat}, {loc.block} BLOCK <span>•</span> {loc.district}
            </div>
          </div>
          <div style={{ fontSize: '14px', color: '#5b7c70', fontWeight: 500 }}>
            {tVal.lastUpdated}
          </div>
        </div>
      </div>

      {/* Main Container */}
      <main className="container">
        
        {/* Agricultural Advisory Section */}
        <div className="advisory">
          <div className="advisory-top">
            <div>
              <p className="eyebrow">{tVal.recHeader}</p>
              <h3>{tVal.advisoryText}</h3>
            </div>
            <span className="priority">HIGH PRIORITY</span>
          </div>
          <p className="advisory-note">{tVal.advisoryNote}</p>
        </div>

        {/* System Information Grid */}
        <div className="info-grid">
          <div className="info-card">
            <span>{tVal.cropLabel}</span>
            <strong>{tVal.cropVal}</strong>
          </div>
          <div className="info-card">
            <span>{tVal.stageLabel}</span>
            <strong>{tVal.stageVal}</strong>
          </div>
          <div className="info-card">
            <span>{tVal.sourceLabel}</span>
            <strong>{tVal.sourceVal}</strong>
          </div>
        </div>

        {/* Weather Metrics Grid */}
        <div className="dashboard">
          <div className="forecast-heading">
            <div>
              <p className="eyebrow">{tVal.currentWeatherHeader.toUpperCase()}</p>
              <h2>{loc.panchayat} Conditions</h2>
            </div>
          </div>

          <div className="forecast-grid">
            <div className="metric-card">
              <div className="metric-top">
                <p>TEMPERATURE</p>
                <div className="metric-icon">🌡️</div>
              </div>
              <span className="metric-value">29<span>°C</span></span>
              <small>Feels like 32°C (Partly Cloudy)</small>
            </div>

            <div className="metric-card">
              <div className="metric-top">
                <p>{tVal.rainProb.toUpperCase()}</p>
                <div className="metric-icon">🌧️</div>
              </div>
              <span className="metric-value">72<span>%</span></span>
              <div className="probability-bar">
                <div className="probability-fill" style={{ width: '72%' }}></div>
              </div>
              <small>Expected rainfall: 4.2 mm</small>
            </div>

            <div className="metric-card">
              <div className="metric-top">
                <p>{tVal.windSpeed.toUpperCase()}</p>
                <div className="metric-icon">💨</div>
              </div>
              <span className="metric-value">10<span>km/h</span></span>
              <small>Humidity: 78% | AQI: Good</small>
            </div>
          </div>
        </div>

        {/* Real Leaflet Map Section */}
        <div style={{ marginTop: '40px' }}>
          <div style={{ background: 'white', border: '1px solid #d9e4de', borderRadius: '24px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '16px', fontWeight: '800', color: '#082b20' }}>📍 {tVal.neighborStatus}</span>
              <span style={{ fontSize: '13px', color: '#0284c7', fontWeight: 'bold', cursor: 'pointer' }}>{tVal.viewOnMap} →</span>
            </div>
            
            <div style={{ height: '320px', width: '100%', borderRadius: '16px', overflow: 'hidden', border: '1px solid #d9e4de' }}>
              <MapContainer 
                center={centerPosition} 
                zoom={11} 
                scrollWheelZoom={false} 
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {locations.map((locItem, idx) => (
                  <Marker key={idx} position={locItem.pos} icon={DefaultIcon}>
                    <Popup>
                      <strong>{locItem.name}</strong><br />
                      Status: {locItem.risk}
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer>
        <p>{tVal.offlineNotice} <span>•</span> PanchMausam SIH Project</p>
      </footer>
    </div>
  );
}