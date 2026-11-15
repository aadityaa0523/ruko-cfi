"""Languages Ruko speaks: the browser's speech code and the spoken warning (numbers in spoken form).

Speech recognition and speech output both run in the user's browser (Web Speech API), so the server needs no
speech API key. The server only scores text.
"""
import os
from pathlib import Path

LANGS = {
    "hi-en": {"bcp": "hi-IN", "warning": "Ruko! Yeh call dhokha lag rahi hai. Bank, police ya sarkar kabhi phone par O T P "
                         "ya paise nahi maangte. Phone kaat dijiye, aur ek nau teen shunya par call kijiye."},
    "hi-IN": {"bcp": "hi-IN", "warning": "रुकिए! यह कॉल धोखा लग रही है। बैंक, पुलिस या सरकार कभी फ़ोन पर ओ टी पी या पैसे नहीं "
                         "माँगते। फ़ोन काट दीजिए, और एक नौ तीन शून्य पर कॉल कीजिए।"},
    "kn-IN": {"bcp": "kn-IN", "warning": "ನಿಲ್ಲಿ! ಇದು ವಂಚನೆಯ ಕರೆ ಅಂತ ಅನಿಸುತ್ತಿದೆ. ಬ್ಯಾಂಕ್, ಪೊಲೀಸ್ ಅಥವಾ ಸರ್ಕಾರ ಯಾವತ್ತೂ ಫೋನಿನಲ್ಲಿ ಒ ಟಿ ಪಿ ಅಥವಾ ಹಣ "
                         "ಕೇಳುವುದಿಲ್ಲ. ಕರೆ ಕಟ್ ಮಾಡಿ, ಒಂದು ಒಂಬತ್ತು ಮೂರು ಸೊನ್ನೆಗೆ ಕರೆ ಮಾಡಿ."},
    "te-IN": {"bcp": "te-IN", "warning": "ఆగండి! ఇది మోసపు కాల్ లాగా ఉంది. బ్యాంక్, పోలీసులు లేదా ప్రభుత్వం ఎప్పుడూ ఫోన్‌లో ఓ టి పి లేదా డబ్బు "
                         "అడగరు. కాల్ కట్ చేసి, ఒకటి తొమ్మిది మూడు సున్నాకి కాల్ చేయండి."},
    "ta-IN": {"bcp": "ta-IN", "warning": "நிறுத்துங்கள்! இது மோசடி அழைப்பு போல் தெரிகிறது. வங்கியோ, காவல்துறையோ, அரசாங்கமோ ஒருபோதும் "
                         "தொலைபேசியில் ஓ டி பி அல்லது பணம் கேட்காது. அழைப்பைத் துண்டித்து, ஒன்று ஒன்பது மூன்று "
                         "பூஜ்ஜியம் என்ற எண்ணை அழையுங்கள்."},
    # Marathi, Bengali, Gujarati, Malayalam: warning text drafted without a native review yet.
    "mr-IN": {"bcp": "mr-IN", "warning": "थांबा! हा कॉल फसवणुकीचा वाटतो. बँक, पोलीस किंवा सरकार कधीही फोनवर ओ टी पी किंवा पैसे मागत नाहीत. "
                         "फोन कट करा, आणि एक नऊ तीन शून्य वर कॉल करा."},
    "bn-IN": {"bcp": "bn-IN", "warning": "থামুন! এই কলটি প্রতারণা মনে হচ্ছে। ব্যাংক, পুলিশ বা সরকার কখনও ফোনে ও টি পি বা টাকা চায় না। "
                         "ফোন কেটে দিন, আর এক নয় তিন শূন্যে কল করুন।"},
    "gu-IN": {"bcp": "gu-IN", "warning": "રોકાઓ! આ કૉલ છેતરપિંડી લાગે છે. બેંક, પોલીસ કે સરકાર ક્યારેય ફોન પર ઓ ટી પી કે પૈસા માંગતી નથી. "
                         "ફોન કાપી નાખો, અને એક નવ ત્રણ શૂન્ય પર કૉલ કરો."},
    "ml-IN": {"bcp": "ml-IN", "warning": "നിൽക്കൂ! ഈ കോൾ തട്ടിപ്പാണെന്ന് തോന്നുന്നു. ബാങ്കോ പോലീസോ സർക്കാരോ ഒരിക്കലും ഫോണിൽ ഒ ടി പി യോ പണമോ ചോദിക്കില്ല. "
                         "ഫോൺ കട്ട് ചെയ്യൂ, ഒന്ന് ഒമ്പത് മൂന്ന് പൂജ്യം എന്ന നമ്പറിൽ വിളിക്കൂ."},
    "en-IN": {"bcp": "en-IN", "warning": "Stop! This call looks like a scam. Banks, police and the government never ask for an "
                         "O T P or money on the phone. Hang up, and call one nine three zero."},
}


def valid_lang(lang: str) -> bool:
    return lang in LANGS


def say_text(lang: str) -> str:
    """What the browser voice reads. Hindi voices read Devanagari far better than romanised Hinglish."""
    return LANGS["hi-IN" if lang == "hi-en" else lang]["warning"]


def load_env(path: Path) -> None:
    """Minimal .env loader so secrets never have to be typed into code or chat."""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
