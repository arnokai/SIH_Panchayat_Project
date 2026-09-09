// src/components/AdvisoryView.jsx
import React, { useState } from 'react';

export default function AdvisoryView({ forecast, locationData, lang, t, onReturnHome }) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Multilingual labels for the advisory view specifically
  const strings = {
    en: {
      title: "Agro-Advisory & Farm Management",
      subtitle: "Expert recommendations customized for your panchayat and current weather conditions.",
      allCategories: "All Advisories",
      pestControl: "Pest & Disease",
      irrigation: "Irrigation",
      fertilizer: "Fertilizer",
      livestock: "Livestock & Shelter",
      priorityHigh: "High Priority",
      priorityMedium: "Medium Priority",
      validUntil: "Valid for next 48 hours",
      readAloud: "Listen to Audio Advisory",
      stopAudio: "Stop Audio",
      shareAdvice: "Share via WhatsApp",
      cropStage: "Current Crop Stage",
      recommendedAction: "Recommended Action",
      localAdvisoryNotice: "Advisories are automatically generated based on block weather models and local agricultural extension data.",
      noAdvisories: "No advisories found for this category."
    },
    bn: {
      title: "কৃষি পরামর্শ ও খামার ব্যবস্থাপনা",
      subtitle: "আপনার পঞ্চায়েত এবং বর্তমান আবহাওয়ার উপর ভিত্তি করে বিশেষজ্ঞদের তৈরি পরামর্শ।",
      allCategories: "সকল পরামর্শ",
      pestControl: "পোকামাকড় ও রোগ",
      irrigation: "জল সেচ",
      fertilizer: "সার প্রয়োগ",
      livestock: "গবাদি পশু ও আশ্রয়",
      priorityHigh: "উচ্চ অগ্রাধিকার",
      priorityMedium: "মাঝারি অগ্রাধিকার",
      validUntil: "আগামী ৪৮ ঘণ্টার জন্য প্রযোজ্য",
      readAloud: "অডিও পরামর্শ শুনুন",
      stopAudio: "অডিও বন্ধ করুন",
      shareAdvice: "হোয়াটসঅ্যাপে শেয়ার করুন",
      cropStage: "ফসলের বর্তমান পর্যায়",
      recommendedAction: "করণীয় পদক্ষেপ",
      localAdvisoryNotice: "এই পরামর্শগুলি ব্লক স্তরের আবহাওয়া এবং স্থানীয় কৃষি দপ্তরের তথ্যের ওপর ভিত্তি করে তৈরি।",
      noAdvisories: "এই বিভাগে কোনো পরামর্শ পাওয়া যায়নি।"
    },
    hi: {
      title: "कृषि सलाह और खेत प्रबंधन",
      subtitle: "आपकी पंचायत और वर्तमान मौसम की स्थिति के अनुसार विशेषज्ञ सलाह।",
      allCategories: "सभी सलाह",
      pestControl: "कीट एवं रोग",
      irrigation: "सिंचाई",
      fertilizer: "उर्वरक",
      livestock: "पशुधन एवं आश्रय",
      priorityHigh: "उच्च प्राथमिकता",
      priorityMedium: "मध्यम प्राथमिकता",
      validUntil: "अगले 48 घंटों के लिए वैध",
      readAloud: "ऑडियो सलाह सुनें",
      stopAudio: "ऑडियो बंद करें",
      shareAdvice: "व्हाट्सएप पर शेयर करें",
      cropStage: "फसल की वर्तमान अवस्था",
      recommendedAction: "सुझाए गए कदम",
      localAdvisoryNotice: "ये सलाह ब्लॉक-स्तरीय मौसम और स्थानीय कृषि डेटा के आधार पर स्वचालित रूप से तैयार की जाती हैं।",
      noAdvisories: "इस श्रेणी में कोई सलाह नहीं मिली।"
    }
  };

  const st = strings[lang] || strings.en;

  // Rich mock advisory entries tailored to local farming & user context
  const advisories = [
    {
      id: 1,
      category: 'irrigation',
      priority: 'high',
      title_en: "Rainfall Expected - Stop Irrigation",
      title_bn: "বৃষ্টির সম্ভাবনা - সেচ দেওয়া বন্ধ রাখুন",
      title_hi: "बारिश की संभावना - सिंचाई रोकें",
      desc_en: "Light to moderate rainfall (2-4mm) is forecasted over the next 48 hours. Postpone any planned irrigation for paddy and vegetable fields to prevent waterlogging.",
      desc_bn: "আগামী ৪৮ ঘণ্টায় হালকা থেকে মাঝারি বৃষ্টির (২-৪ মিমি) সম্ভাবনা রয়েছে। জল জমার হাত থেকে রক্ষা করতে ধান ও সবজি জমিতে সেচ দেওয়া স্থগিত রাখুন।",
      desc_hi: "अगले 48 घंटों में हल्की से मध्यम बारिश (2-4 मिमी) की संभावना है। जलभराव को रोकने के लिए धान और सब्जी के खेतों में सिंचाई स्थगित करें।",
      crop_en: "Paddy, Jute, Summer Vegetables",
      crop_bn: "ধান, পাট, গ্রীষ্মকালীন সবজি",
      crop_hi: "धान, जूट, ग्रीष्मकालीन सब्जियां",
      date: "29 May 2026"
    },
    {
      id: 2,
      category: 'pestControl',
      priority: 'high',
      title_en: "High Humidity Blast Risk Alert",
      title_bn: "উচ্চ আর্দ্রতার কারণে ব্লাস্ট রোগের সতর্কতা",
      title_hi: "उच्च आर्द्रता के कारण ब्लास्ट रोग की चेतावनी",
      desc_en: "Current humidity levels exceed 78% with cloudy skies, creating ideal conditions for fungal blast in paddy. Monitor leaves and apply Tricyclazole if lesions appear.",
      desc_bn: "বর্তমান আর্দ্রতা ৭৮% এর বেশি এবং আকাশ মেঘলা থাকায় ধানে ছত্রাকজনিত ব্লাস্ট রোগের অনুকূল পরিবেশ তৈরি হয়েছে। পাতা পরীক্ষা করুন এবং প্রয়োজন হলে ট্রাইসাইক্লাজল স্প্রে করুন।",
      desc_hi: "वर्तमान आर्द्रता 78% से अधिक है और आसमान में बादल हैं, जिससे धान में फंगस ब्लास्ट का खतरा है। पत्तियों की जाँच करें।"
    },
    {
      id: 3,
      category: 'fertilizer',
      priority: 'medium',
      title_en: "Split Application of Nitrogen Fertilizer",
      title_bn: "নাইট্রোজেন সার কিস্তিতে প্রয়োগ করুন",
      title_hi: "नाइट्रोजन उर्वरक का विभाजित प्रयोग",
      desc_en: "Apply the second dose of urea fertilizer only after the upcoming rain spell clears. Applying before heavy rain will wash away nutrients.",
      desc_bn: "আসন্ন বৃষ্টির পর আবহাওয়া পরিষ্কার হলে ইউরিয়া সারের দ্বিতীয় কিস্তি প্রয়োগ করুন। বৃষ্টির আগে দিলে পুষ্টি উপাদান ধুয়ে যেতে পারে।",
      desc_hi: "आगामी बारिश के बाद ही यूरिया उर्वरक की दूसरी खुराक दें। भारी बारिश से पहले डालने पर पोषक तत्व बह सकते हैं।"
    },
    {
      id: 4,
      category: 'livestock',
      priority: 'medium',
      title_en: "Pet & Livestock Shelter Protection",
      title_bn: "পশুসম্পদ ও পশুর আশ্রয়ের সুরক্ষা",
      title_hi: "पशुधन और पालतू पशुओं के आश्रय की सुरक्षा",
      desc_en: "Ensure animal sheds and covered enclosures (such as bunny housing hutches) are protected from damp winds and accumulated standing mud during incoming rains.",
      desc_bn: "বৃষ্টির সময় পশুর শেড এবং ঢাকা ঘেরগুলি আর্দ্র বাতাস ও জলকাদা থেকে সুরক্ষিত রাখুন।",
      desc_hi: "आने वाली बारिश के दौरान यह सुनिश्चित करें कि पशु शेड और बाड़े नम हवा और कीचड़ से सुरक्षित रहें।"
    }
  ];

  const filteredAdvisories = selectedCategory === 'all' 
    ? advisories 
    : advisories.filter(item => item.category === selectedCategory);

  const toggleAudio = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    } else {
      if ('speechSynthesis' in window) {
        const textToRead = filteredAdvisories.map(a => lang === 'bn' ? a.desc_bn : a.desc_en).join('. ');
        const utterance = new SpeechSynthesisUtterance(textToRead);
        utterance.lang = lang === 'bn' ? 'bn-IN' : lang === 'hi' ? 'hi-IN' : 'en-US';
        utterance.onend = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
        setIsSpeaking(true);
      } else {
        alert("Text-to-speech not supported in this browser.");
      }
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full animate-fadeIn">
      
      {/* Header Banner */}
      <div className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🍃</span>
            <h2 className="text-2xl font-extrabold text-[#082b20]">{st.title}</h2>
          </div>
          <p className="text-xs sm:text-sm text-[#54786b]">{st.subtitle}</p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={toggleAudio}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold shadow-xs transition cursor-pointer ${
              isSpeaking 
                ? 'bg-amber-500 text-white animate-pulse' 
                : 'bg-[#1e5c3a] text-white hover:bg-[#16472d]'
            }`}
          >
            <span>{isSpeaking ? '⏹️' : '🔊'}</span>
            <span>{isSpeaking ? st.stopAudio : st.readAloud}</span>
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: 'all', label: st.allCategories, icon: '📋' },
          { id: 'irrigation', label: st.irrigation, icon: '💧' },
          { id: 'pestControl', label: st.pestControl, icon: '🐛' },
          { id: 'fertilizer', label: st.fertilizer, icon: '🧪' },
          { id: 'livestock', label: st.livestock, icon: '🏡' },
        ].map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedCategory === cat.id 
                ? 'bg-[#1e5c3a] text-white shadow-sm' 
                : 'bg-white border border-[#d7e2dc] text-[#54786b] hover:bg-slate-50'
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Advisory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filteredAdvisories.length === 0 ? (
          <div className="col-span-2 bg-white border border-[#d7e2dc] rounded-3xl p-10 text-center text-slate-500 text-sm">
            {st.noAdvisories}
          </div>
        ) : (
          filteredAdvisories.map(item => (
            <div 
              key={item.id} 
              className="bg-white border border-[#d7e2dc] rounded-3xl p-6 shadow-xs flex flex-col justify-between transition hover:shadow-md"
            >
              <div>
                <div className="flex justify-between items-center mb-3">
                  <span className={`text-[10px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider ${
                    item.priority === 'high' 
                      ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                      : 'bg-amber-100 text-amber-800 border border-amber-200'
                  }`}>
                    {item.priority === 'high' ? st.priorityHigh : st.priorityMedium}
                  </span>
                  <span className="text-[11px] text-[#54786b] font-medium">📅 {item.date}</span>
                </div>

                <h3 className="text-base sm:text-lg font-extrabold text-[#082b20] mb-2">
                  {lang === 'bn' ? item.title_bn : lang === 'hi' ? item.title_hi : item.title_en}
                </h3>

                <p className="text-xs sm:text-sm text-[#334e44] leading-relaxed mb-4">
                  {lang === 'bn' ? item.desc_bn : lang === 'hi' ? item.desc_hi : item.desc_en}
                </p>

                {item.crop_en && (
                  <div className="bg-[#f8faf9] border border-[#e2e8e5] p-3 rounded-2xl text-xs mb-4">
                    <span className="font-bold text-[#54786b] block mb-0.5">{st.cropStage}</span>
                    <span className="font-extrabold text-[#082b20]">
                      {lang === 'bn' ? item.crop_bn : lang === 'hi' ? item.crop_hi : item.crop_en}
                    </span>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-[#edf3ef] flex items-center justify-between">
                <span className="text-[11px] text-[#6a8479] font-medium">⏱️ {st.validUntil}</span>
                <button 
                  onClick={() => alert(`Shared advisory: ${item.title_en}`)}
                  className="text-xs font-bold text-emerald-700 hover:text-emerald-900 flex items-center gap-1.5 cursor-pointer bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200"
                >
                  <span>💬</span> {st.shareAdvice}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Notice */}
      <div className="bg-[#edf6ef] border border-[#cfe0d4] p-4 rounded-2xl text-xs text-[#1e5c3a] flex items-center gap-3">
        <span className="text-lg">💡</span>
        <span>{st.localAdvisoryNotice}</span>
      </div>

    </div>
  );
}