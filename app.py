import os
import json
import random
from typing import List, Optional

import streamlit as st
from openai import OpenAI

# =====================================================
# 🎁 GIFT AI – STREAMLIT ÖN YÜZ
# =====================================================

st.set_page_config(
    page_title="GiftAI – Akıllı Hediye Asistanı",
    page_icon="🎁",
    layout="centered",
)

# --------- GLOBAL STİL (DARK, KART GÖRÜNÜMÜ) ----------
st.markdown(
    """
<style>
    .stApp {
        background: radial-gradient(circle at top, #111827 0, #020617 45%, #000 100%);
        color: #e5e7eb;
    }
    .block-container {
        max-width: 880px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        font-weight: 700;
    }
    .gift-section {
        background: rgba(15,23,42,0.9);
        border-radius: 18px;
        padding: 18px 22px;
        border: 1px solid rgba(55,65,81,0.9);
        margin-bottom: 18px;
        box-shadow: 0 12px 25px rgba(0,0,0,0.35);
    }
    .gift-badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 11px;
        border-radius: 999px;
        background: linear-gradient(90deg,#22c55e,#16a34a);
        color: white;
        text-transform: uppercase;
        letter-spacing: .06em;
        margin-bottom: 4px;
    }
    .gift-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
    }
    .score-label {
        font-size: 0.8rem;
        margin-bottom: 3px;
        color: #e5e7eb;
    }
    .score-track {
        width: 100%;
        background: #020617;
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
        border: 1px solid #111827;
    }
    .score-fill {
        height: 100%;
        border-radius: inherit;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<span class='gift-badge'>beta</span>",
    unsafe_allow_html=True,
)
st.title("🎁 GiftAI – Akıllı Hediye Asistanı")
st.markdown(
    "<p class='gift-subtitle'>Sevgilin, arkadaşın veya başka biri için birkaç soruyu cevapla; GiftAI senin yerine beyin fırtınası yapsın.</p>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------
# 🔐 OPENAI API AYARI
# -----------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY bulunamadı.\n\n"
        "Streamlit Cloud'da bu uygulamayı kullanmak için, "
        "app ayarlarından **Secrets** kısmına `OPENAI_API_KEY` eklemen gerekiyor."
    )
    st.stop()

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------------------------------
# ✅ MODELLER
# -----------------------------------------------------
class Recipient:
    def __init__(
        self,
        age: Optional[int],
        gender: Optional[str],
        relationship: Optional[str],
        hobbies: List[str],
        style_tags: List[str],
    ):
        self.age = age
        self.gender = gender
        self.relationship = relationship
        self.hobbies = hobbies
        self.style_tags = style_tags


class RecommendRequest:
    def __init__(
        self,
        recipient: Recipient,
        purpose: str,
        risk_level: str,
        urgency: str,
        budget_min: Optional[float],
        budget_max: Optional[float],
        free_text: str,
        top_n: int,
    ):
        self.recipient = recipient
        self.purpose = purpose
        self.risk_level = risk_level
        self.urgency = urgency
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.free_text = free_text
        self.top_n = top_n


# -----------------------------------------------------
# 🎯 ÜRÜN KATALOĞU
# -----------------------------------------------------
PRODUCT_CATALOG = [
    {
        "id": "yoga_set",
        "name": "Renkli Premium Yoga Seti",
        "category": "wellness",
        "base_price": 4500,
        "tags": ["spor", "yoga", "sağlık", "kendine_zaman", "wellness"],
        "base_description": "Yoga matı, blok ve kaydırmaz çorap içeren konforlu set.",
    },
    {
        "id": "vinyl_player",
        "name": "Retro Pikap ve Plak Seti",
        "category": "music",
        "base_price": 5500,
        "tags": ["müzik", "retro", "dekorasyon", "ev"],
        "base_description": "Vintage tasarımlı pikap ve sevilen türde başlangıç plakları.",
    },
    {
        "id": "photo_album",
        "name": "Kişisel Fotoğraf Albümü",
        "category": "memory",
        "base_price": 900,
        "tags": ["fotoğraf", "anı", "kişiselleştirilebilir", "romantik"],
        "base_description": "Beraber çekildiğiniz fotoğraflarla doldurulabilecek şık albüm.",
    },
    {
        "id": "spa_day",
        "name": "Çiftlere Spa ve Masaj Günü",
        "category": "experience",
        "base_price": 3200,
        "tags": ["deneyim", "romantik", "rahatlama", "spa"],
        "base_description": "Spa giriş, sauna ve çift masajı içeren dinlendirici deneyim.",
    },
    {
        "id": "kindle",
        "name": "Kindle Paperwhite Okuyucu",
        "category": "tech",
        "base_price": 6500,
        "tags": ["kitap", "teknoloji", "okuma", "seyahat"],
        "base_description": "Kitap kurdu hediyesi, onlarca kitabı tek cihazda taşıma keyfi.",
    },
    {
        "id": "airpods",
        "name": "Apple AirPods Kulaklık",
        "category": "tech",
        "base_price": 7500,
        "tags": ["müzik", "teknoloji", "günlük", "apple"],
        "base_description": "Günlük kullanımda konforlu, kablosuz kulaklık.",
    },
    {
        "id": "coffee_set",
        "name": "3. Nesil Kahve Deneyim Seti",
        "category": "coffee",
        "base_price": 1800,
        "tags": ["kahve", "gurme", "ev", "hobi"],
        "base_description": "Özel çekirdek kahveler ve pour-over ekipmanı içeren set.",
    },
    {
        "id": "polaroid",
        "name": "Instax Mini Anlık Fotoğraf Makinesi",
        "category": "photo",
        "base_price": 3500,
        "tags": ["fotoğraf", "anı", "eğlence", "arkadaş"],
        "base_description": "Anıları anında baskıya döken eğlenceli fotoğraf makinesi.",
    },
    {
        "id": "corporate_box",
        "name": "Premium Ofis Hediye Kutusu",
        "category": "corporate",
        "base_price": 1500,
        "tags": ["kurumsal", "ofis", "nötr", "şık"],
        "base_description": "Ajanda, metal kalem ve kahve kupası içeren zarif kutu.",
    },
    {
        "id": "smart_mug",
        "name": "Akıllı Isı Korumalı Kupa",
        "category": "tech",
        "base_price": 2100,
        "tags": ["ofis", "teknoloji", "kahve", "hediye"],
        "base_description": "İçeceğin sıcaklığını uzun süre sabit tutan akıllı kupa.",
    },
]


def generate_price(base_price: int) -> float:
    factor = random.uniform(0.9, 1.15)
    price = base_price * factor
    return float(int(round(price / 10.0) * 10))


def build_profile_tone(purpose: str, relationship: Optional[str]) -> str:
    if relationship == "partner" or purpose == "romantik":
        return "romantik"
    if purpose == "kurumsal" or relationship == "colleague":
        return "kurumsal"
    if purpose == "ozur":
        return "telafi"
    return "nötr"


def build_description(product: dict, req: RecommendRequest) -> str:
    tone = build_profile_tone(req.purpose, req.recipient.relationship)
    target_map = {
        "partner": "sevgilin veya eşin",
        "friend": "yakın arkadaşın",
        "parent": "annen ya da baban",
        "sibling": "kardeşin",
        "colleague": "iş arkadaşın",
        "other": "hediye almak istediğin kişi",
        None: "hediye almak istediğin kişi",
    }
    hedef = target_map.get(req.recipient.relationship, target_map[None])

    base = product["base_description"]

    if tone == "romantik":
        return (
            f"{hedef} için düşünülmüş, birlikte anı biriktirmeyi ön plana çıkaran "
            f"romantik bir seçenek. {base}"
        )
    if tone == "kurumsal":
        return (
            "İş ortamında rahatlıkla verilebilecek, şık ama risksiz bir ofis hediyesi. "
            f"{base}"
        )
    if tone == "telafi":
        return (
            f"Küçük bir jestle ortamı yumuşatmak ve gönül almak için uygun bir tercih. "
            f"{base}"
        )
    return f"Günlük hayatta kullanılabilir, çoğu kişinin seveceği güvenli bir tercih. {base}"


def compute_weights(req: RecommendRequest) -> dict:
    w_interest = 0.4
    w_emotion = 0.4
    w_budget = 0.2

    if req.purpose == "romantik" or req.recipient.relationship == "partner":
        w_emotion += 0.15
        w_budget -= 0.1

    if req.purpose == "kurumsal" or req.recipient.relationship == "colleague":
        w_budget += 0.15
        w_emotion -= 0.1

    if req.risk_level == "cesur":
        w_interest += 0.05
        w_emotion += 0.05
        w_budget -= 0.1
    elif req.risk_level == "guvenli":
        w_budget += 0.1
        w_emotion -= 0.05

    total = w_interest + w_emotion + w_budget
    return {
        "interest": w_interest / total,
        "emotion": w_emotion / total,
        "budget": w_budget / total,
    }


def call_openai_scoring(req: RecommendRequest, products: List[dict]) -> dict:
    profile = {
        "age": req.recipient.age,
        "gender": req.recipient.gender,
        "relationship": req.recipient.relationship,
        "purpose": req.purpose,
        "risk_level": req.risk_level,
        "urgency": req.urgency,
        "hobbies": req.recipient.hobbies,
        "style_tags": req.recipient.style_tags,
        "free_text": req.free_text,
        "budget_min": req.budget_min,
        "budget_max": req.budget_max,
    }

    system_prompt = (
        "You are a scoring engine for a gift recommender system.\n"
        "Given a user profile and a list of candidate gifts, you ONLY return JSON "
        "with numeric scores between 0 and 1 for:\n"
        "- interest_score: How well the gift matches hobbies/style/profile.\n"
        "- emotion_score: How strong and memorable the emotional impact is.\n"
        "- budget_score: How well the gift fits the budget and context (corporate vs romantic).\n\n"
        "Rules:\n"
        "- Return a JSON object with key 'scores', value is a list.\n"
        "- Each item has: id, interest_score, emotion_score, budget_score.\n"
        "- Do NOT generate gift names, prices or descriptions.\n"
        "- Scores must be floats between 0.0 and 1.0.\n"
    )

    user_payload = {
        "profile": profile,
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "tags": p["tags"],
                "base_price": p["base_price"],
            }
            for p in products
        ],
    }

    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            max_output_tokens=600,
        )
        raw = response.output[0].content[0].text  # type: ignore
        data = json.loads(raw)
        scores_list = data.get("scores", [])
    except Exception:
        # Model hata verirse hepsine nötr skor
        scores_list = [
            {
                "id": p["id"],
                "interest_score": 0.7,
                "emotion_score": 0.7,
                "budget_score": 0.7,
            }
            for p in products
        ]

    scores_by_id = {}
    for item in scores_list:
        try:
            pid = item["id"]
            scores_by_id[pid] = {
                "interest_score": float(item.get("interest_score", 0.7)),
                "emotion_score": float(item.get("emotion_score", 0.7)),
                "budget_score": float(item.get("budget_score", 0.7)),
            }
        except Exception:
            continue
    return scores_by_id


# -----------------------------------------------------
# 🧾 FORM – KULLANICI GİRDİLERİ
# -----------------------------------------------------
with st.container():
    st.markdown("<div class='gift-section'>", unsafe_allow_html=True)

    st.subheader("👤 Hediye Alınacak Kişi")

    col1, col2 = st.columns(2)

    with col1:
        gender = st.selectbox("Cinsiyet", ["Bilmiyorum / Söylemek istemiyorum", "Kadın", "Erkek"])
        age = st.number_input("Yaş", min_value=10, max_value=90, value=25, step=1)

    with col2:
        relationship = st.selectbox(
            "İlişkiniz",
            [
                "Sevgili / Eş",
                "Yakın arkadaş",
                "Aile (anne/baba)",
                "Kardeş",
                "İş arkadaşı",
                "Diğer",
            ],
        )

    purpose = st.selectbox(
        "Hediye amacı",
        [
            "Doğum günü",
            "Romantik jest / yıldönümü",
            "Yeni başlangıç (yeni iş, taşınma vb.)",
            "Gönül alma / özür",
            "Kurumsal / iş odaklı",
            "Öylesine, içimden geldi",
        ],
    )

    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='gift-section'>", unsafe_allow_html=True)

    # -------------------- HOBİLER (SERBEST METİN, ÇOKLU) --------------------
    st.subheader("🎨 Hobiler & İlgi Alanları")

    if "hobbies" not in st.session_state:
        st.session_state["hobbies"] = []

    hobby_input = st.text_input(
        "Hobi ekle (örn: resim çizmek, paten, anime izlemek…)",
        key="hobby_input",
    )
    col_h1, col_h2 = st.columns([1, 3])
    with col_h1:
        if st.button("Hobi ekle"):
            if hobby_input.strip():
                st.session_state["hobbies"].append(hobby_input.strip())
                st.session_state["hobby_input"] = ""

    if st.session_state["hobbies"]:
        st.write("Eklenen hobiler:")
        for h in st.session_state["hobbies"]:
            st.write(f"• {h}")

    st.markdown("---")

    # -------------------- STİL / TARZ (SERBEST METİN, ÇOKLU) --------------------
    st.subheader("✨ Stil / Tarz")

    if "styles" not in st.session_state:
        st.session_state["styles"] = []

    style_input = st.text_input(
        "Stil ekle (örn: pastel tonlar, sade, retro…)",
        key="style_input",
    )
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        if st.button("Stil ekle"):
            if style_input.strip():
                st.session_state["styles"].append(style_input.strip())
                st.session_state["style_input"] = ""

    if st.session_state["styles"]:
        st.write("Eklenen stiller:")
        for s in st.session_state["styles"]:
            st.write(f"• {s}")

    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='gift-section'>", unsafe_allow_html=True)

    st.subheader("💸 Bütçe ve Tercihler")

    col3, col4 = st.columns(2)
    with col3:
        budget_min = st.number_input(
            "Minimum bütçe (TL)", min_value=0, max_value=100000, value=500, step=100
        )
    with col4:
        budget_max = st.number_input(
            "Maksimum bütçe (TL)", min_value=0, max_value=100000, value=3000, step=100
        )

    risk_level = st.selectbox(
        "Hediye tarzı seçimin",
        [
            "Güvenli (herkesin seveceği)",
            "Normal (bir tık kişiye özel)",
            "Cesur (daha iddialı, riskli)",
        ],
    )

    urgency = st.selectbox(
        "Ne kadar acil?",
        [
            "Esnek, zamanım var",
            "Birkaç gün içinde lazım",
            "Bugün / yarın hemen lazım",
        ],
    )

    free_text = st.text_area(
        "Eklemek istediğin özel notlar (isteğe bağlı)",
        placeholder="Örn: Daha önce parfüm hoşuna gitmemişti, ortak anılarımıza vurgu olsa iyi olur...",
    )

    top_n = st.slider("Kaç farklı hediye fikri görmek istersin?", min_value=1, max_value=5, value=3)

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------- MAP FONKSİYONLARI ---------------------
def map_relationship(val: str) -> str:
    if val.startswith("Sevgili"):
        return "partner"
    if val.startswith("Yakın arkadaş"):
        return "friend"
    if val.startswith("Aile"):
        return "parent"
    if val.startswith("Kardeş"):
        return "sibling"
    if val.startswith("İş arkadaşı"):
        return "colleague"
    return "other"


def map_purpose(val: str) -> str:
    if val.startswith("Doğum günü"):
        return "dogum_gunu"
    if val.startswith("Romantik"):
        return "romantik"
    if val.startswith("Yeni başlangıç"):
        return "yeni_baslangic"
    if val.startswith("Gönül alma"):
        return "ozur"
    if val.startswith("Kurumsal"):
        return "kurumsal"
    return "icimden_geldi"


def map_risk(val: str) -> str:
    if val.startswith("Güvenli"):
        return "guvenli"
    if val.startswith("Cesur"):
        return "cesur"
    return "normal"


def map_urgency(val: str) -> str:
    if val.startswith("Birkaç gün"):
        return "few_days"
    if val.startswith("Bugün"):
        return "same_day"
    return "flexible"


# --------------------- SKOR BAR RENDERER ---------------------
def render_score_bar(label: str, value: float, color: str):
    pct = max(0, min(int(value * 100), 100))
    st.markdown(
        f"""
        <div class="score-label">{label}: <b>{value:.2f}</b></div>
        <div class="score-track">
            <div class="score-fill" style="width:{pct}%;background:{color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------
# 🚀 ÖNERİ BUTONU
# -----------------------------------------------------
if st.button("🎁 Hediye Önerilerini Getir"):
    with st.spinner("Hediye fikirleri hazırlanıyor..."):
        hobbies = st.session_state.get("hobbies", [])
        style_tags = st.session_state.get("styles", [])

        recipient = Recipient(
            age=int(age) if age else None,
            gender=gender.lower(),
            relationship=map_relationship(relationship),
            hobbies=hobbies,
            style_tags=style_tags,
        )

        req = RecommendRequest(
            recipient=recipient,
            purpose=map_purpose(purpose),
            risk_level=map_risk(risk_level),
            urgency=map_urgency(urgency),
            budget_min=float(budget_min) if budget_min else None,
            budget_max=float(budget_max) if budget_max else None,
            free_text=free_text,
            top_n=int(top_n),
        )

        # Bütçeye göre ürünleri filtrele
        filtered_products = []
        for p in PRODUCT_CATALOG:
            price = generate_price(p["base_price"])
            if req.budget_min and price < req.budget_min * 0.6:
                continue
            if req.budget_max and price > req.budget_max * 1.4:
                continue
            filtered_products.append({**p, "price": price})

        if not filtered_products:
            filtered_products = [
                {**p, "price": generate_price(p["base_price"])} for p in PRODUCT_CATALOG
            ]

        scores_by_id = call_openai_scoring(req, filtered_products)
        weights = compute_weights(req)

        results = []
        for p in filtered_products:
            sc = scores_by_id.get(
                p["id"],
                {"interest_score": 0.7, "emotion_score": 0.7, "budget_score": 0.7},
            )

            final_score = (
                sc["interest_score"] * weights["interest"]
                + sc["emotion_score"] * weights["emotion"]
                + sc["budget_score"] * weights["budget"]
            )

            desc = build_description(p, req)
            results.append(
                {
                    "name": p["name"],
                    "description": desc,
                    "price": p["price"],
                    "scores": sc,
                    "final_score": final_score,
                }
            )

        results_sorted = sorted(results, key=lambda x: x["final_score"], reverse=True)[: req.top_n]

    st.subheader("🎯 Senin için seçilen hediye fikirleri")

    for r in results_sorted:
        st.markdown("<div class='gift-section'>", unsafe_allow_html=True)
        st.markdown(f"### 🎁 {r['name']}")
        st.markdown(f"**Tahmini Fiyat:** {int(r['price'])} TL")
        st.write(r["description"])

        with st.expander("Detaylı skorlar"):
            render_score_bar("İlgi uyumu", r["scores"]["interest_score"], "linear-gradient(90deg,#22c55e,#4ade80)")
            render_score_bar("Duygusal etki", r["scores"]["emotion_score"], "linear-gradient(90deg,#ec4899,#f97316)")
            render_score_bar("Bütçe uyumu", r["scores"]["budget_score"], "linear-gradient(90deg,#38bdf8,#6366f1)")
            render_score_bar("Genel skor", r["final_score"], "linear-gradient(90deg,#a855f7,#22c55e)")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

