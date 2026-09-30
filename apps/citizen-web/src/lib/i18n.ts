export type Lang = "en" | "hi" | "pa";

export const LANGS: { code: Lang; name: string }[] = [
  { code: "en", name: "English" },
  { code: "hi", name: "हिन्दी" },
  { code: "pa", name: "ਪੰਜਾਬੀ" },
];

const STRINGS = {
  subtitle: {
    en: "Report pollution in seconds. Help officers act faster.",
    hi: "कुछ ही सेकंड में प्रदूषण की सूचना दें। अधिकारियों को जल्दी कार्रवाई में मदद करें।",
    pa: "ਕੁਝ ਸਕਿੰਟਾਂ ਵਿੱਚ ਪ੍ਰਦੂਸ਼ਣ ਦੀ ਸੂਚਨਾ ਦਿਓ। ਅਧਿਕਾਰੀਆਂ ਨੂੰ ਜਲਦੀ ਕਾਰਵਾਈ ਵਿੱਚ ਮਦਦ ਕਰੋ।",
  },
  where: { en: "1. Your location", hi: "1. आपका स्थान", pa: "1. ਤੁਹਾਡਾ ਟਿਕਾਣਾ" },
  useMyLocation: { en: "Use my location", hi: "मेरा स्थान लें", pa: "ਮੇਰਾ ਟਿਕਾਣਾ ਵਰਤੋ" },
  photo: { en: "2. Photo of the pollution", hi: "2. प्रदूषण की फ़ोटो", pa: "2. ਪ੍ਰਦੂਸ਼ਣ ਦੀ ਫ਼ੋਟੋ" },
  takePhoto: { en: "Take or upload a photo", hi: "फ़ोटो लें या अपलोड करें", pa: "ਫ਼ੋਟੋ ਲਓ ਜਾਂ ਅੱਪਲੋਡ ਕਰੋ" },
  orSample: { en: "or use a sample photo (demo):", hi: "या नमूना फ़ोटो चुनें (डेमो):", pa: "ਜਾਂ ਨਮੂਨਾ ਫ਼ੋਟੋ ਚੁਣੋ (ਡੈਮੋ):" },
  describe: {
    en: "Optional: what do you see?",
    hi: "वैकल्पिक: आप क्या देख रहे हैं?",
    pa: "ਵਿਕਲਪਿਕ: ਤੁਸੀਂ ਕੀ ਦੇਖ ਰਹੇ ਹੋ?",
  },
  searchPlace: {
    en: "Search a locality (Google Maps)",
    hi: "इलाका खोजें (Google Maps)",
    pa: "ਇਲਾਕਾ ਲੱਭੋ (Google Maps)",
  },
  search: { en: "Search", hi: "खोजें", pa: "ਲੱਭੋ" },
  recordVoice: { en: "🎙 Speak instead", hi: "🎙 बोलकर बताएँ", pa: "🎙 ਬੋਲ ਕੇ ਦੱਸੋ" },
  stopVoice: { en: "■ Stop and transcribe", hi: "■ रोकें और लिखें", pa: "■ ਰੋਕੋ ਅਤੇ ਲਿਖੋ" },
  submit: { en: "Submit report", hi: "रिपोर्ट भेजें", pa: "ਰਿਪੋਰਟ ਭੇਜੋ" },
  submitting: { en: "Checking photo…", hi: "फ़ोटो जाँची जा रही है…", pa: "ਫ਼ੋਟੋ ਜਾਂਚੀ ਜਾ ਰਹੀ ਹੈ…" },
  result: { en: "Your report", hi: "आपकी रिपोर्ट", pa: "ਤੁਹਾਡੀ ਰਿਪੋਰਟ" },
  localAir: { en: "Air near you", hi: "आपके पास की हवा", pa: "ਤੁਹਾਡੇ ਨੇੜੇ ਦੀ ਹਵਾ" },
  advisory: { en: "Health advisory", hi: "स्वास्थ्य सलाह", pa: "ਸਿਹਤ ਸਲਾਹ" },
  listen: { en: "Listen", hi: "सुनें", pa: "ਸੁਣੋ" },
  noAdvisory: {
    en: "No approved advisory for your area yet.",
    hi: "आपके क्षेत्र के लिए अभी कोई स्वीकृत सलाह नहीं है।",
    pa: "ਤੁਹਾਡੇ ਖੇਤਰ ਲਈ ਅਜੇ ਕੋਈ ਪ੍ਰਵਾਨਿਤ ਸਲਾਹ ਨਹੀਂ ਹੈ।",
  },
  myReports: { en: "My reports", hi: "मेरी रिपोर्टें", pa: "ਮੇਰੀਆਂ ਰਿਪੋਰਟਾਂ" },
  thanks: {
    en: "Thank you. Your report was checked and added to the local evidence.",
    hi: "धन्यवाद। आपकी रिपोर्ट जाँची गई और स्थानीय साक्ष्य में जोड़ी गई।",
    pa: "ਧੰਨਵਾਦ। ਤੁਹਾਡੀ ਰਿਪੋਰਟ ਜਾਂਚੀ ਗਈ ਅਤੇ ਸਥਾਨਕ ਸਬੂਤਾਂ ਵਿੱਚ ਜੋੜੀ ਗਈ।",
  },
  sentToOfficer: {
    en: "Sent to the environmental officer for review",
    hi: "समीक्षा के लिए पर्यावरण अधिकारी को भेजा गया",
    pa: "ਸਮੀਖਿਆ ਲਈ ਵਾਤਾਵਰਣ ਅਧਿਕਾਰੀ ਨੂੰ ਭੇਜਿਆ ਗਿਆ",
  },
} satisfies Record<string, Record<Lang, string>>;

export type StringKey = keyof typeof STRINGS;

export function t(key: StringKey, lang: Lang): string {
  return STRINGS[key][lang];
}
