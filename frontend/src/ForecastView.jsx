import React from 'react';

export default function ForecastView({ forecast, locationData, lang, onReturnHome, t }) {
  if (!forecast) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      
      {/* Top Location Bar */}
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        border: '1px solid #e2e8f0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            onClick={onReturnHome}
            style={{
              background: '#0d9488',
              color: '#ffffff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px'
            }}
          >
            ← {t.returnHome || "Return to Home Dashboard"}
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a', fontWeight: '700' }}>
            <span style={{ color: '#0d9488', fontSize: '18px' }}>📍</span>
            <span>{locationData?.panchayat || forecast.panchayat_name}, {forecast.block}</span>
            <span style={{ color: '#64748b', fontWeight: '400', fontSize: '14px' }}>{forecast.district}, West Bengal</span>
          </div>
        </div>
        <div style={{ fontSize: '13px', color: '#64748b' }}>
          {t.updated}: {forecast.updated_at} 🔄
        </div>
      </div>

      {/* Main Two-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px' }}>
        
        {/* LEFT COLUMN: Advisories & Impact */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Main Advisory Card */}
          <div style={{
            background: 'linear-gradient(135deg, #e6f4ea 0%, #f0fdf4 100%)',
            borderRadius: '20px',
            padding: '24px',
            border: '1px solid #bbf7d0',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <span style={{
              background: '#15803d',
              color: '#ffffff',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '700'
            }}>
              {lang === 'hi' ? 'आज के लिए अनुशंसित कदम' : lang === 'bn' ? 'আজকের জন্য সুপারিশকৃত পদক্ষেপ' : 'Recommended Action for Today'}
            </span>
            <h2 style={{ fontSize: '22px', color: '#064e3b', margin: '16px 0 10px 0', fontWeight: '800' }}>
              {lang === 'en' ? forecast.advisory?.text_en : forecast.advisory?.text_bn}
            </h2>
            <p style={{ margin: 0, color: '#166534', fontSize: '14px', lineHeight: '1.5' }}>
              {t.rainAlert}
            </p>
          </div>

          {/* Crop, Stage & Audio Player */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr', gap: '12px' }}>
            <div style={{ background: '#fff', padding: '16px', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', color: '#166534', fontWeight: '700' }}>🌱 {lang === 'hi' ? 'फसल' : lang === 'bn' ? 'ফসল' : 'Crop'}</div>
              <div style={{ fontSize: '16px', fontWeight: '800', marginTop: '4px', color: '#0f172a' }}>ধান (Rice)</div>
            </div>
            <div style={{ background: '#fff', padding: '16px', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', color: '#166534', fontWeight: '700' }}>🌱 {lang === 'hi' ? 'फसल चरण' : lang === 'bn' ? 'ফসলের পর্যায়' : 'Crop Stage'}</div>
              <div style={{ fontSize: '16px', fontWeight: '800', marginTop: '4px', color: '#0f172a' }}>{lang === 'hi' ? 'विकास चरण' : lang === 'bn' ? 'বৃদ্ধি পর্যায়' : 'Vegetative Stage'}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>(Vegetative Stage)</div>
            </div>
            <button style={{
              background: '#059669',
              color: 'white',
              border: 'none',
              borderRadius: '16px',
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '15px'
            }}>
              🔊 {t.listen} ({lang === 'en' ? 'Listen' : lang === 'hi' ? 'सुने' : 'শুনুন'})
            </button>
          </div>

          {/* Source & Timestamp */}
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            padding: '16px 20px',
            border: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontSize: '12px', color: '#64748b' }}>🏛️ {lang === 'hi' ? 'स्रोत' : lang === 'bn' ? 'উৎস' : 'Source'}</span>
              <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '14px' }}>কৃষি বিজ্ঞান কেন্দ্র (KVK), উত্তর ২৪ পরগনা</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '12px', color: '#64748b' }}>📅 {lang === 'hi' ? 'दिनांक और समय' : lang === 'bn' ? 'তারিখ ও সময়' : 'Date & Time'}</span>
              <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '14px' }}>29 May 2025, {forecast.updated_at}</div>
            </div>
          </div>

          {/* High Risk Alert Banner */}
          <div style={{
            background: '#fff7ed',
            border: '1px solid #ffedd5',
            borderRadius: '16px',
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ color: '#ea580c', fontSize: '20px' }}>⚠️</span>
              <div>
                <strong style={{ color: '#c2410c', display: 'block', fontSize: '14px' }}>{t.highPriority}</strong>
                <span style={{ color: '#9a3412', fontSize: '13px' }}>
                  {lang === 'hi' ? 'यह एक उच्च जोखिम वाली मौसम चेतावनी है। किसान/कृषि विभाग की आधिकारिक समीक्षा आवश्यक है।' : lang === 'bn' ? 'এটি একটি উচ্চ ঝুঁকির আবহাওয়া সতর্কতা। কৃষক/কৃষি দপ্তরের অফিসিয়াল পর্যালোচনা প্রয়োজন।' : 'This is a high-risk weather alert. Official review by the agriculture department is required.'}
                </span>
              </div>
            </div>
            <button style={{
              background: '#fff',
              border: '1px solid #fdba74',
              color: '#c2410c',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: '700',
              cursor: 'pointer'
            }}>
              🛡️ {lang === 'hi' ? 'आधिकारिक समीक्षा आवश्यक' : lang === 'bn' ? 'অফিসিয়াল পর্যালোচনা প্রয়োজন' : 'Official Review Needed'}
            </button>
          </div>

          {/* Additional Info Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ background: '#f0fdf4', padding: '16px', borderRadius: '16px', border: '1px solid #dcfce7' }}>
              <div style={{ fontWeight: '700', color: '#166534', marginBottom: '8px', fontSize: '14px' }}>🌱 {lang === 'hi' ? 'संभावित प्रभाव' : lang === 'bn' ? 'সম্ভাব্য প্রভাব' : 'Potential Impact'}</div>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#15803d', fontSize: '13px', lineHeight: '1.6' }}>
                <li>{lang === 'hi' ? 'अतिरिक्त पानी जमने से धान के पौधे खराब हो सकते हैं।' : lang === 'bn' ? 'অতিরিক্ত জল জমলে ধানের চারা নষ্ট হতে পারে।' : 'Waterlogging may damage paddy seedlings.'}</li>
                <li>{lang === 'hi' ? 'फंगस संक्रमण का खतरा बढ़ सकता है।' : lang === 'bn' ? 'ছত্রাকের সংক্রমণের ঝুঁকি বাড়তে পারে।' : 'Risk of fungal infections may increase.'}</li>
              </ul>
            </div>
            <div style={{ background: '#f0fdf4', padding: '16px', borderRadius: '16px', border: '1px solid #dcfce7' }}>
              <div style={{ fontWeight: '700', color: '#166534', marginBottom: '8px', fontSize: '14px' }}>💡 {lang === 'hi' ? 'अतिरिक्त सलाह' : lang === 'bn' ? 'অতিরিক্ত পরামর্শ' : 'Additional Advice'}</div>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#15803d', fontSize: '13px', lineHeight: '1.6' }}>
                <li>{lang === 'hi' ? 'यदि खेत में पानी जमा है, तो तुरंत पानी निकालने की व्यवस्था करें।' : lang === 'bn' ? 'জমিতে জল জমে থাকলে দ্রুত নিকাশির ব্যবস্থা করুন।' : 'Ensure prompt drainage if water accumulates in the field.'}</li>
                <li>{lang === 'hi' ? 'यदि आवश्यक हो तो जैविक फफूंदनाशक का प्रयोग करें।' : lang === 'bn' ? 'প্রয়োজনে জৈব ছত্রাকনাশক ব্যবহার করুন।' : 'Use organic fungicide if necessary.'}</li>
              </ul>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Weather Metrics & 5-Day Forecast */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Current Weather Grid */}
          <div style={{ background: '#fff', borderRadius: '20px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: '700', color: '#0f172a', marginBottom: '16px', fontSize: '15px' }}>
              🌧️ {t.currentWeather} ({forecast.panchayat_name})
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '36px', fontWeight: '800', color: '#0f172a' }}>{forecast.current?.temp}°C</span>
                <div style={{ fontSize: '13px', color: '#64748b' }}>{lang === 'en' ? forecast.current?.condition_en : forecast.current?.condition_bn}</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>💧 {t.rainProb}</span>
                  <div style={{ fontWeight: '700', color: '#0f172a' }}>{forecast.current?.rain_prob}%</div>
                </div>
                <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>💨 {lang === 'hi' ? 'हवा की गति' : lang === 'bn' ? 'বাতাসের গতি' : 'Wind Speed'}</span>
                  <div style={{ fontWeight: '700', color: '#0f172a' }}>{forecast.current?.wind_speed} km/h</div>
                </div>
                <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>💦 {t.humidity}</span>
                  <div style={{ fontWeight: '700', color: '#0f172a' }}>{forecast.current?.humidity}%</div>
                </div>
                <div style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>🌡️ {t.temperature}</span>
                  <div style={{ fontWeight: '700', color: '#0f172a' }}>{forecast.current?.temp}° / {forecast.current?.feels_like}°C</div>
                </div>
              </div>
            </div>
          </div>

          {/* 5-Day Forecast */}
          <div style={{ background: '#fff', borderRadius: '20px', padding: '20px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: '700', color: '#0f172a', marginBottom: '14px', fontSize: '15px' }}>
              📅 {t.fiveDayForecast}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px' }}>
              {forecast.daily_forecast?.map((item, idx) => (
                <div key={idx} style={{
                  background: idx === 0 ? '#f0fdf4' : '#ffffff',
                  border: idx === 0 ? '1px solid #86efac' : '1px solid #f1f5f9',
                  borderRadius: '12px',
                  padding: '8px 4px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#0f172a' }}>{lang === 'en' ? item.day_en : item.day_bn}</div>
                  <div style={{ fontSize: '10px', color: '#64748b' }}>{item.date}</div>
                  <div style={{ fontSize: '18px', margin: '4px 0' }}>{item.icon}</div>
                  <div style={{ fontSize: '10px', fontWeight: '700' }}>{item.temp_max}°/{item.temp_min}°</div>
                  <div style={{ fontSize: '10px', color: '#0284c7' }}>💧 {item.rain_prob}%</div>
                </div>
              ))}
            </div>
          </div>

          {/* Mini Panchayat Status */}
          <div style={{ background: '#fff', borderRadius: '20px', padding: '16px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>📍 {forecast.panchayat_name} ({forecast.block} Block)</span>
              <span style={{ fontSize: '12px', color: '#0284c7', fontWeight: '600', cursor: 'pointer' }}>View on Map</span>
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', lineHeight: '1.4' }}>
              {lang === 'hi' ? 'आसपास की पंचायतें: कुछ पंचायतों में बारिश की संभावना अधिक है, कुछ में कम।' : lang === 'bn' ? 'পাশের পঞ্চায়েতের অবস্থা: বেশ কিছু পঞ্চায়েতে বৃষ্টির সম্ভাবনা বেশি, কয়েকটিতে কম।' : 'Adjacent Panchayats: Higher rain probability in some panchayats, lower in others.'}
            </div>
          </div>

          {/* Offline Indicator Bar */}
          <div style={{
            background: '#f0f9ff',
            border: '1px solid #e0f2fe',
            borderRadius: '12px',
            padding: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <span style={{ fontSize: '16px' }}>📶</span>
            <div style={{ fontSize: '12px', color: '#0369a1' }}>
              <strong>{t.offlineMode}</strong>
              <div>{t.cachedData}. {t.updated}: {forecast.updated_at}</div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}