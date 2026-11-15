// Ready-made WhatsApp messages. {url} is replaced with this site's own address, so the same page works anywhere it is hosted.
// The translations are machine-drafted and want a native read; the English text is the reference.
const MESSAGES = {
  quiz: {
    path: "/quiz/",
    text: {
      English: "Can you spot a scam message? Take this 2-minute test and learn the 4 signs scammers use. It's free: {url}",
      "हिन्दी": "क्या आप धोखे वाला मैसेज पहचान सकते हैं? 2 मिनट का यह टेस्ट दें और ठगों के 4 तरीके सीखें। मुफ़्त है: {url}",
      "தமிழ்": "மோசடி செய்தியை உங்களால் கண்டுபிடிக்க முடியுமா? இந்த 2 நிமிட சோதனையை எடுத்து மோசடிக்காரர்களின் 4 அடையாளங்களைத் தெரிந்துகொள்ளுங்கள். இலவசம்: {url}",
      "తెలుగు": "మోసపు సందేశాన్ని మీరు గుర్తించగలరా? ఈ 2 నిమిషాల పరీక్ష రాసి మోసగాళ్ల 4 సూచనలు తెలుసుకోండి. ఉచితం: {url}",
      "ಕನ್ನಡ": "ಮೋಸದ ಸಂದೇಶವನ್ನು ನೀವು ಗುರುತಿಸಬಲ್ಲಿರಾ? ಈ 2 ನಿಮಿಷದ ಪರೀಕ್ಷೆ ಬರೆದು ಮೋಸಗಾರರ 4 ಲಕ್ಷಣಗಳನ್ನು ತಿಳಿಯಿರಿ. ಉಚಿತ: {url}",
      "मराठी": "फसवणुकीचा मेसेज तुम्ही ओळखू शकता का? ही 2 मिनिटांची चाचणी द्या आणि फसवणूक करणाऱ्यांच्या 4 खुणा शिका. मोफत: {url}",
      "বাংলা": "প্রতারণার মেসেজ কি আপনি চিনতে পারেন? এই ২ মিনিটের পরীক্ষা দিন আর প্রতারকদের ৪টি চিহ্ন শিখুন। বিনামূল্যে: {url}",
    },
  },
  check: {
    path: "/check/",
    text: {
      English: "Got a strange SMS, WhatsApp message, link or UPI request? Paste it here and Ruko tells you in seconds if it's a scam. Free, nothing is stored: {url}",
      "हिन्दी": "कोई अजीब SMS, WhatsApp मैसेज, लिंक या UPI रिक्वेस्ट आया? यहाँ चिपकाइए, Ruko सेकंडों में बता देगा कि यह धोखा है या नहीं। मुफ़्त, कुछ सेव नहीं होता: {url}",
      "தமிழ்": "விசித்திரமான SMS, WhatsApp செய்தி, லிங்க் அல்லது UPI கோரிக்கை வந்ததா? இங்கே ஒட்டுங்கள், இது மோசடியா என்று Ruko சில விநாடிகளில் சொல்லும். இலவசம், எதுவும் சேமிக்கப்படாது: {url}",
      "తెలుగు": "వింత SMS, WhatsApp సందేశం, లింక్ లేదా UPI అభ్యర్థన వచ్చిందా? ఇక్కడ పేస్ట్ చేయండి, ఇది మోసమో కాదో Ruko సెకన్లలో చెబుతుంది. ఉచితం, ఏదీ సేవ్ కాదు: {url}",
      "ಕನ್ನಡ": "ವಿಚಿತ್ರ SMS, WhatsApp ಸಂದೇಶ, ಲಿಂಕ್ ಅಥವಾ UPI ವಿನಂತಿ ಬಂದಿದೆಯೇ? ಇಲ್ಲಿ ಅಂಟಿಸಿ, ಇದು ಮೋಸವೇ ಎಂದು Ruko ಸೆಕೆಂಡುಗಳಲ್ಲಿ ಹೇಳುತ್ತದೆ. ಉಚಿತ, ಏನೂ ಸಂಗ್ರಹವಾಗುವುದಿಲ್ಲ: {url}",
      "मराठी": "विचित्र SMS, WhatsApp मेसेज, लिंक किंवा UPI विनंती आली आहे का? इथे पेस्ट करा, हा फसवणुकीचा प्रकार आहे का ते Ruko काही सेकंदांत सांगेल. मोफत, काहीही साठवले जात नाही: {url}",
      "বাংলা": "অদ্ভুত SMS, WhatsApp মেসেজ, লিংক বা UPI অনুরোধ এসেছে? এখানে পেস্ট করুন, এটা প্রতারণা কি না Ruko কয়েক সেকেন্ডে বলে দেবে। বিনামূল্যে, কিছুই সংরক্ষিত হয় না: {url}",
    },
  },
};

let which = "quiz";
function render() {
  const m = MESSAGES[which], url = location.origin + m.path;
  $("cards").innerHTML = "";
  for (const [lang, tpl] of Object.entries(m.text)) {
    const msg = tpl.replace("{url}", url);
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = '<h3></h3><p class="msg"></p><div class="row"><a class="btn btn-primary" target="_blank" rel="noopener">Send on WhatsApp</a><button class="btn btn-plain" type="button">Copy</button></div>';
    card.querySelector("h3").textContent = lang;
    card.querySelector(".msg").textContent = msg;
    card.querySelector("a").href = "https://wa.me/?text=" + encodeURIComponent(msg);
    const copy = card.querySelector("button");
    copy.onclick = async () => {
      try { await navigator.clipboard.writeText(msg); copy.textContent = "Copied"; } catch { copy.textContent = "Select the text above"; }
      setTimeout(() => (copy.textContent = "Copy"), 2000);
    };
    $("cards").append(card);
  }
}
for (const [id, key] of [["tabQuiz", "quiz"], ["tabCheck", "check"]]) {
  $(id).onclick = () => { which = key; $("tabQuiz").setAttribute("aria-pressed", String(key === "quiz")); $("tabCheck").setAttribute("aria-pressed", String(key === "check")); render(); };
}
render();
