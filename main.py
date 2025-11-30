# main.py
import os
import json
import random
import logging
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import OpenAI

# -------------------------------------------------
# 1. AYARLAR
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("giftai")

# 🔐 OPENAI API KEY AYARI (GitHub için güvenli)
# Sadece ortam değişkeninden okuyoruz. Örn:
# - Windows PowerShell:  setx OPENAI_API_KEY "sk-xxx"
# - .env dosyası:        OPENAI_API_KEY=sk-xxx  (ve .env'i .gitignore'a ekle)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OPENAI_API_KEY bulundu, gerçek skorlayıcı aktif.")
else:
    openai_client = None
    logger.warning(
        "OPENAI_API_KEY bulunamadı. OpenAI skoru yerine nötr fallback skorları kullanılacak."
    )

app = FastAPI(title="GiftAI Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # İstersen burayı daha kısıtlı yap
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 2. MODELLER
# -------------------------------------------------
class Recipient(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    relationship: Optional[str] = None  # partner, friend, parent, sibling, colleague, other
    hobbies: List[str] = []
    style_tags: List[str] = []


class RecommendRequest(BaseModel):
    recipient: Recipient
    purpose: str              # dogum_gunu, romantik, yeni_baslangic, ozur, kurumsal, icimden_geldi
    risk_level: str           # guvenli | normal | cesur
    urgency: str              # flexible | few_days | same_day
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    free_text: Optional[str] = ""
    top_n: int = 3


class ScoreBlock(BaseModel):
    interest_score: float
    emotion_score: float
    budget_score: float


class GiftResult(BaseModel):
    name: str
    description: str
    price: float
    scores: ScoreBlock
    final_score: float


class RecommendResponse(BaseModel):
    results: List[GiftResult]


# -------------------------------------------------
# 3. ÜRÜN KATALOĞU (GERÇEKÇİ HEDİYE TİPLERİ)
# -------------------------------------------------
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
    """Base price etrafında makul bir TL fiyat üret."""
    factor = random.uniform(0.9, 1.15)
    price = base_price * factor
    # 10 TL yuvarla ve float olarak döndür
    return float(int(round(price / 10.0) * 10))


# -------------------------------------------------
# 4. YARDIMCI FONKSİYONLAR
# -------------------------------------------------
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
    # nötr
    return f"Günlük hayatta kullanılabilir, çoğu kişinin sevebileceği güvenli bir tercih. {base}"


def compute_weights(req: RecommendRequest) -> dict:
    # Varsayılan ağırlıklar
    w_interest = 0.4
    w_emotion = 0.4
    w_budget = 0.2

    # Romantik / partner -> duygusal ağırlık
    if req.purpose == "romantik" or req.recipient.relationship == "partner":
        w_emotion += 0.15
        w_budget -= 0.1

    # Kurumsal / colleague -> bütçe + nötr
    if req.purpose == "kurumsal" or req.recipient.relationship == "colleague":
        w_budget += 0.15
        w_emotion -= 0.1

    # Risk seviyesine göre ayar
    if req.risk_level == "cesur":
        w_interest += 0.05
        w_emotion += 0.05
        w_budget -= 0.1
    elif req.risk_level == "guvenli":
        w_budget += 0.1
        w_emotion -= 0.05

    # Normalizasyon
    total = w_interest + w_emotion + w_budget
    return {
        "interest": w_interest / total,
        "emotion": w_emotion / total,
        "budget": w_budget / total,
    }


def call_openai_scoring(req: RecommendRequest, products: List[dict]) -> dict:
    """
    OpenAI'den her ürün için interest / emotion / budget skorlarını al.
    Dönen dict: {product_id: {"interest_score":..., "emotion_score":..., "budget_score":...}}
    """
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

    # Eğer OpenAI client yoksa (key yoksa) direkt fallback'e geç
    if openai_client is None:
        logger.warning("OpenAI client yok, nötr skorlarla devam ediliyor.")
        scores_list = [
            {
                "id": p["id"],
                "interest_score": 0.7,
                "emotion_score": 0.7,
                "budget_score": 0.7,
            }
            for p in products
        ]
    else:
        try:
            response = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False),
                    },
                ],
                max_output_tokens=600,
            )
            raw = response.output[0].content[0].text  # type: ignore
            data = json.loads(raw)
            scores_list = data.get("scores", [])
        except Exception as e:
            logger.warning(f"OpenAI scoring failed, using fallback neutral scores. Error: {e}")
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


# -------------------------------------------------
# 5. ENDPOINT
# -------------------------------------------------
@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    top_n = max(1, min(req.top_n, 5))

    # Bütçeye göre ürünleri kabaca filtrele (çok uçları at)
    filtered_products = []
    for p in PRODUCT_CATALOG:
        price = generate_price(p["base_price"])
        if req.budget_min and price < req.budget_min * 0.6:
            continue
        if req.budget_max and price > req.budget_max * 1.4:
            continue
        filtered_products.append({**p, "price": price})

    if not filtered_products:
        # Hiç bulunamazsa hepsini kullan
        filtered_products = [
            {**p, "price": generate_price(p["base_price"])} for p in PRODUCT_CATALOG
        ]

    scores_by_id = call_openai_scoring(req, filtered_products)
    weights = compute_weights(req)

    results: List[GiftResult] = []
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
            GiftResult(
                name=p["name"],
                description=desc,
                price=p["price"],
                scores=ScoreBlock(**sc),
                final_score=final_score,
            )
        )

    # Skora göre sırala, top_n al
    results_sorted = sorted(results, key=lambda x: x.final_score, reverse=True)[
        :top_n
    ]

    top3_names = [r.name for r in results_sorted]
    logger.info(
        "[GiftAI] Öneri üretildi - purpose=%s, relationship=%s, risk=%s, urgency=%s, top_n=%s, top3=%s",
        req.purpose,
        req.recipient.relationship,
        req.risk_level,
        req.urgency,
        top_n,
        top3_names,
    )

    return RecommendResponse(results=results_sorted)
