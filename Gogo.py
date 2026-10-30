import os
import re
import json
import time
import random
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import requests
import telebot
from telebot import types
from cachetools import TTLCache

TOKEN = os.getenv('BOT_TOKEN', '9129471263:AAE0aAXEnww8QPNs6012hDopqRKAlqCxaYY')
ACTIVATION_GROUP = -5506570535
BOT_USERNAME = '@OctiNetbot'
REGISTERED_NUMBERS_FILE = 'registered_numbers.json'

# إعدادات الاشتراك الإجباري والمطور
REQUIRED_CHANNEL = '@OctiNet'
DEVELOPER_URL = 'https://t.me/sud0_dev'

if not TOKEN or TOKEN == 'PUT_YOUR_NEW_BOT_TOKEN_HERE':
    raise RuntimeError('❌ ضـع تـوكـن الـبـوت الـجـديـد فـي الـمـتـغـيـر BOT_TOKEN أو داخـل TOKEN.')

logging.basicConfig(
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('djezzy_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NexsBot')

bot = telebot.TeleBot(TOKEN, parse_mode='HTML', threaded=True)
executor = ThreadPoolExecutor(max_workers=20)

user_sessions = {}
user_numbers = {}
pending_otp_resend = {}
processing_users = set()

otp_cache = TTLCache(maxsize=100, ttl=60)
token_cache = TTLCache(maxsize=100, ttl=3600)
balance_cache = TTLCache(maxsize=100, ttl=120)

OFFER_CODES = {
    'weekly': 'GIFTWALKWIN2GO',
    'shake_4gb': 'BTLINTSPEEDDAY2Go',
    'imtiyaz_90da_5gb': 'BTL500MBDAY',
    'imtiyaz_190da_10gb': 'BTL4GBDAY',
    'imtiyaz_800da': 'BTLHYBMONTHLY800DA',
    'imtiyaz_1000da': 'BTLHYBMONTHLY1000DA',
    'imtiyaz_1200da': 'BTLHYBMONTHLY1200DA',
    'imtiyaz_1500da': 'BTLHYBMONTHLY1500DA',
    'imtiyaz_2000da': 'BTL2C2000',
    'izzy_1200': 'OFFREJEUNE1200',
    'izzy_500': 'OFFREJEUNEBASE500',
    'izzy_300': 'OFFREJEUNEBASE300',
    'izzy_50': 'OFFREJEUNE50',
    'option_500': 'OPTION500',
    'zid_1000': 'lowValue1000',
    'zid_800': 'lowValue800',
    'zid_400': 'lowValue400',
    'zid_200': 'lowValue200',
    'zid_50': 'lowValue50',
    'hayla_bezzef_2000': 'HAYLABEZZEFMONTH2000PREP',
    'hayla_bezzef_1500': 'HAYLABEZZEFMONTH1500PREP',
    'hayla_bezzef_1200': 'HAYLABEZZEFMONTH1200PREP',
    'hayla_bezzef_500': 'HAYLABEZZEFWEEK500PREP',
    'hayla_bezzef_150': 'HAYLABEZZEFDAILY150PREP',
    'hayla_bezzef_100': 'HAYLABEZZEFDAY100PREP',
    'hayla_maxi_2000': 'MAXIHAYLA2000',
    'hayla_maxi_1500': 'MAXIHAYLA1500',
    'hayla_maxi_1200': 'MAXIHAYLA1200',
    'hayla_maxi_500': 'MAXIHAYLA500',
    'hayla_maxi_100': 'MAXIHAYLA100'
}

FREE_OFFERS = {
    'weekly': {'offer_id': 'weekly', 'name': '🌟 2GB أُسـبـوعـي', 'code': OFFER_CODES['weekly'], 'amount': '2GB', 'type': 'weekly', 'category': 'free', 'price': 'مـجـانـي', 'price_dzd': 0, 'duration': '24 سـاعـة', 'emoji': '🌟', 'button_text': '🌟 2GB أُسـبـوعـي', 'display_name': '2GB', 'description': '2 جـيـغـا مـجـانـيـة.'}
}

IMTIYAZ_OFFERS = {
    'shake_4gb': {'name': '⚡ 70 DA - 4 GB', 'code': OFFER_CODES['shake_4gb'], 'amount': '4GB', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '70 DA', 'price_dzd': 70, 'duration': '24 سـاعـة', 'emoji': '⚡', 'button_text': '⚡ 70 DA', 'display_name': '4GB', 'description': '4 جـيـغـا بـ 70 دج صـالـحـة 24 سـاعـة.'},
    'imtiyaz_90da_5gb': {'name': '⚡ 90 DA - 5 GB', 'code': OFFER_CODES['imtiyaz_90da_5gb'], 'amount': '5GB', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '90 DA', 'price_dzd': 90, 'duration': '24 سـاعـة', 'emoji': '⚡', 'button_text': '⚡ 90 DA', 'display_name': '5GB', 'description': '5 جـيـغـا بـ 90 دج صـالـحـة 24 سـاعـة.'},
    'imtiyaz_190da_10gb': {'name': '🔥 190 DA - 10 GB', 'code': OFFER_CODES['imtiyaz_190da_10gb'], 'amount': '10GB', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '190 DA', 'price_dzd': 190, 'duration': '3 أيـام', 'emoji': '🔥', 'button_text': '🔥 190 DA', 'display_name': '10GB', 'description': '10 جـيـغـا بـ 190 دج صـالـحـة 3 أيـام.'},
    'imtiyaz_800da': {'name': '👑 IMTIYAZ 800 DA', 'code': OFFER_CODES['imtiyaz_800da'], 'amount': '15GB + 2000 دج', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '800 DA', 'price_dzd': 800, 'duration': '30 يـوم', 'emoji': '👑', 'button_text': '👑 800 DA', 'display_name': '15GB+2000DA', 'description': '15GB + 2000 دج + مـكـالـمـات غـيـر مـحـدودة.'},
    'imtiyaz_1000da': {'name': '👑 IMTIYAZ 1000 DA', 'code': OFFER_CODES['imtiyaz_1000da'], 'amount': '20GB + 3000 دج', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '1000 DA', 'price_dzd': 1000, 'duration': '30 يـوم', 'emoji': '👑', 'button_text': '👑 1000 DA', 'display_name': '20GB+3000DA', 'description': '20GB + 3000 دج + مـكـالـمـات غـيـر مـحـدودة.'},
    'imtiyaz_1200da': {'name': '👑 IMTIYAZ 1200 DA', 'code': OFFER_CODES['imtiyaz_1200da'], 'amount': '30GB + 2500 دج', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '1200 DA', 'price_dzd': 1200, 'duration': '30 يـوم', 'emoji': '👑', 'button_text': '👑 1200 DA', 'display_name': '30GB+2500DA', 'description': '30GB + 2500 دج + مـكـالـمـات غـيـر مـحـدودة.'},
    'imtiyaz_1500da': {'name': '👑 IMTIYAZ 1500 DA', 'code': OFFER_CODES['imtiyaz_1500da'], 'amount': '40GB + 3000 دج', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '1500 DA', 'price_dzd': 1500, 'duration': '30 يـوم', 'emoji': '👑', 'button_text': '👑 1500 DA', 'display_name': '40GB+3000DA', 'description': '40GB + 3000 دج + مـكـالـمـات غـيـر مـحـدودة.'},
    'imtiyaz_2000da': {'name': '👑 IMTIYAZ 2000 DA', 'code': OFFER_CODES['imtiyaz_2000da'], 'amount': '70GB + مـكـالـمـات', 'type': 'imtiyaz', 'category': 'imtiyaz_offers', 'price': '2000 DA', 'price_dzd': 2000, 'duration': '30 يـوم', 'emoji': '👑', 'button_text': '👑 2000 DA', 'display_name': '70GB', 'description': '70GB + مـكـالـمـات غـيـر مـحـدودة وطـنـيـة.'}
}

IZZY_OFFERS = {
    'izzy_1200': {'name': '📦 DJEZZY IZZY 1200', 'code': OFFER_CODES['izzy_1200'], 'amount': '10GB + Illimité', 'type': 'izzy', 'category': 'izzy_offers', 'price': '1200 DA', 'price_dzd': 1200, 'duration': '30 يـوم', 'emoji': '📦', 'button_text': '📦 1200 DA', 'display_name': '10GB+Illimité', 'description': '10GB + إنـتـرنـت غـيـر مـحـدود + 1000 دج كـريـديـت + مـكـالـمـات ورسـائـل غـيـر مـحـدودة نـحـو جـيـزي.'},
    'izzy_500': {'name': '📦 DJEZZY IZZY 500', 'code': OFFER_CODES['izzy_500'], 'amount': '5GB + Insta Illimité', 'type': 'izzy', 'category': 'izzy_offers', 'price': '500 DA', 'price_dzd': 500, 'duration': '30 يـوم', 'emoji': '📦', 'button_text': '📦 500 DA', 'display_name': '5GB+Insta', 'description': '5GB + إنـسـتـغـرام غـيـر مـحـدود + 500 دج كـريـديـت.'},
    'izzy_300': {'name': '📦 DJEZZY IZZY 300', 'code': OFFER_CODES['izzy_300'], 'amount': '3GB', 'type': 'izzy', 'category': 'izzy_offers', 'price': '300 DA', 'price_dzd': 300, 'duration': '15 يـوم', 'emoji': '📦', 'button_text': '📦 300 DA', 'display_name': '3GB', 'description': '3GB إنـتـرنـت + مـكـالـمـات ورسـائـل غـيـر مـحـدودة نـحـو جـيـزي.'},
    'izzy_50': {'name': '📦 DJEZZY IZZY 50', 'code': OFFER_CODES['izzy_50'], 'amount': '1GB', 'type': 'izzy', 'category': 'izzy_offers', 'price': '50 DA', 'price_dzd': 50, 'duration': '24 سـاعـة', 'emoji': '📦', 'button_text': '📦 50 DA', 'display_name': '1GB', 'description': '1GB إنـتـرنـت + مـكـالـمـات ورسـائـل غـيـر مـحـدودة نـحـو جـيـزي.'},
    'option_500': {'name': '📦 DJEZZY IZZY Option 500', 'code': OFFER_CODES['option_500'], 'amount': '5GB + Insta Illimité', 'type': 'izzy', 'category': 'izzy_offers', 'price': '500 DA', 'price_dzd': 500, 'duration': '15 يـوم', 'emoji': '📦', 'button_text': '📦 Option 500', 'display_name': '5GB+Insta', 'description': '5GB + إنـسـتـغـرام غـيـر مـحـدود.'}
}

ZID_OFFERS = {
    'zid_1000': {'name': '⚡ DJEZZY ZID 1000', 'code': OFFER_CODES['zid_1000'], 'amount': '10GB', 'type': 'zid', 'category': 'zid_offers', 'price': '1000 DA', 'price_dzd': 1000, 'duration': '30 يـوم', 'emoji': '⚡', 'button_text': '⚡ 1000 DA', 'display_name': '10GB', 'description': '10GB + 1300 دج كـريـديـت + مـكـالـمـات ورسـائـل غـيـر مـحـدودة نـحـو جـيـزي.'},
    'zid_800': {'name': '⚡ DJEZZY ZID 800', 'code': OFFER_CODES['zid_800'], 'amount': '8GB', 'type': 'zid', 'category': 'zid_offers', 'price': '800 DA', 'price_dzd': 800, 'duration': '30 يـوم', 'emoji': '⚡', 'button_text': '⚡ 800 DA', 'display_name': '8GB', 'description': '8GB + 1000 دج كـريـديـت.'},
    'zid_400': {'name': '⚡ DJEZZY ZID 400', 'code': OFFER_CODES['zid_400'], 'amount': '4GB', 'type': 'zid', 'category': 'zid_offers', 'price': '400 DA', 'price_dzd': 400, 'duration': '15 يـوم', 'emoji': '⚡', 'button_text': '⚡ 400 DA', 'display_name': '4GB', 'description': '4GB + 500 دج كـريـديـت.'},
    'zid_200': {'name': '⚡ DJEZZY ZID 200', 'code': OFFER_CODES['zid_200'], 'amount': '2GB', 'type': 'zid', 'category': 'zid_offers', 'price': '200 DA', 'price_dzd': 200, 'duration': '7 أيـام', 'emoji': '⚡', 'button_text': '⚡ 200 DA', 'display_name': '2GB', 'description': '2GB + 200 دج كـريـديـت.'},
    'zid_50': {'name': '⚡ DJEZZY ZID 50', 'code': OFFER_CODES['zid_50'], 'amount': '500MB', 'type': 'zid', 'category': 'zid_offers', 'price': '50 DA', 'price_dzd': 50, 'duration': '24 سـاعـة', 'emoji': '⚡', 'button_text': '⚡ 50 DA', 'display_name': '500MB', 'description': '500MB + 50 دج كـريـديـت.'}
}

HAYLA_BEZZEF_OFFERS = {
    'hayla_bezzef_2000': {'name': '🔥 HAYLA BEZZEF 2000', 'code': OFFER_CODES['hayla_bezzef_2000'], 'amount': '60GB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '2000 DA', 'price_dzd': 2000, 'duration': '30 يـوم', 'emoji': '🔥', 'button_text': '🔥 2000 DA', 'display_name': '60GB', 'description': '60GB + 7000 دج كـريـديـت + مـكـالـمـات ورسـائـل غـيـر مـحـدودة.'},
    'hayla_bezzef_1500': {'name': '🔥 HAYLA BEZZEF 1500', 'code': OFFER_CODES['hayla_bezzef_1500'], 'amount': '40GB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '1500 DA', 'price_dzd': 1500, 'duration': '30 يـوم', 'emoji': '🔥', 'button_text': '🔥 1500 DA', 'display_name': '40GB', 'description': '40GB + 3000 دج كـريـديـت.'},
    'hayla_bezzef_1200': {'name': '🔥 HAYLA BEZZEF 1200', 'code': OFFER_CODES['hayla_bezzef_1200'], 'amount': '10GB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '1200 DA', 'price_dzd': 1200, 'duration': '30 يـوم', 'emoji': '🔥', 'button_text': '🔥 10GB', 'description': '10GB + 1500 دج كـريـديـت.'},
    'hayla_bezzef_500': {'name': '🔥 HAYLA BEZZEF 500', 'code': OFFER_CODES['hayla_bezzef_500'], 'amount': '3GB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '500 DA', 'price_dzd': 500, 'duration': '15 يـوم', 'emoji': '🔥', 'button_text': '🔥 500 DA', 'display_name': '3GB', 'description': '3GB + 750 دج كـريـديـت.'},
    'hayla_bezzef_150': {'name': '🔥 HAYLA BEZZEF 150', 'code': OFFER_CODES['hayla_bezzef_150'], 'amount': '2GB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '150 DA', 'price_dzd': 150, 'duration': '24 سـاعـة', 'emoji': '🔥', 'button_text': '🔥 150 DA', 'display_name': '2GB', 'description': '2GB + 300 دج كـريـديـت.'},
    'hayla_bezzef_100': {'name': '🔥 HAYLA BEZZEF 100', 'code': OFFER_CODES['hayla_bezzef_100'], 'amount': '500MB', 'type': 'hayla_bezzef', 'category': 'hayla_bezzef_offers', 'price': '100 DA', 'price_dzd': 100, 'duration': '24 سـاعـة', 'emoji': '🔥', 'button_text': '🔥 100 DA', 'display_name': '500MB', 'description': '500MB + 150 دج كـريـديـت.'}
}

HAYLA_MAXI_OFFERS = {
    'hayla_maxi_2000': {'name': '🌟 HAYLA MAXI 2000', 'code': OFFER_CODES['hayla_maxi_2000'], 'amount': '60GB', 'type': 'hayla_maxi', 'category': 'hayla_maxi_offers', 'price': '2000 DA', 'price_dzd': 2000, 'duration': '30 يـوم', 'emoji': '🌟', 'button_text': '🌟 2000 DA', 'display_name': '60GB', 'description': '60GB + 4000 دج كـريـديـت.'},
    'hayla_maxi_1500': {'name': '🌟 HAYLA MAXI 1500', 'code': OFFER_CODES['hayla_maxi_1500'], 'amount': '40GB', 'type': 'hayla_maxi', 'category': 'hayla_maxi_offers', 'price': '1500 DA', 'price_dzd': 1500, 'duration': '30 يـوم', 'emoji': '🌟', 'button_text': '🌟 1500 DA', 'display_name': '40GB', 'description': '40GB + 3000 دج كـريـديـت.'},
    'hayla_maxi_1200': {'name': '🌟 HAYLA MAXI 1200', 'code': OFFER_CODES['hayla_maxi_1200'], 'amount': '12GB', 'type': 'hayla_maxi', 'category': 'hayla_maxi_offers', 'price': '1200 DA', 'price_dzd': 1200, 'duration': '30 يـوم', 'emoji': '🌟', 'button_text': '🌟 1200 DA', 'display_name': '12GB', 'description': '12GB + 1500 دج كـريـديـت.'},
    'hayla_maxi_500': {'name': '🌟 HAYLA MAXI 500', 'code': OFFER_CODES['hayla_maxi_500'], 'amount': '7GB', 'type': 'hayla_maxi', 'category': 'hayla_maxi_offers', 'price': '500 DA', 'price_dzd': 500, 'duration': '7 أيـام', 'emoji': '🌟', 'button_text': '🌟 500 DA', 'display_name': '7GB', 'description': '7GB + 750 دج كـريـديـت.'},
    'hayla_maxi_100': {'name': '🌟 HAYLA MAXI 100', 'code': OFFER_CODES['hayla_maxi_100'], 'amount': '1GB', 'type': 'hayla_maxi', 'category': 'hayla_maxi_offers', 'price': '100 DA', 'price_dzd': 100, 'duration': '24 سـاعـة', 'emoji': '🌟', 'button_text': '🌟 100 DA', 'display_name': '1GB', 'description': '1GB + 150 دج كـريـديـت.'}
}

ALL_OFFERS = {}
for offer_group in (FREE_OFFERS, IMTIYAZ_OFFERS, IZZY_OFFERS, ZID_OFFERS, HAYLA_BEZZEF_OFFERS, HAYLA_MAXI_OFFERS):
    ALL_OFFERS.update(offer_group)

HEADERS = {
    'User-Agent': 'MobileApp/3.0.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'accept-language': 'fr',
    'Connection': 'keep-alive'
}

def check_user_subscription(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logger.error(f'Subscription check error for user {user_id}: {e}')
        return False

def send_force_subscription_message(chat_id: int, message_id: int = None):
    text = (
        "⚠️ <b>عـلـيـك الاِشـتـراك فـي الـقـنـاة أوَّلاً لـاسـتـخـدام الـبـوت:</b>\n\n"
        f"📢 إشـتـرك فـي الـقـنـاة: {REQUIRED_CHANNEL}\n\n"
        "بـعـد الإشـتـراك، إضـغـط عـلـى زِر <b>تـأكـيـد الاِشـتـراك 🔄</b> لـلـبـدء."
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('📢 إشـتـرك فـي الـقـنـاة', url=f'https://t.me/{REQUIRED_CHANNEL.replace("@", "")}', style='primary'),
        types.InlineKeyboardButton('🔄 تـأكـيـد الاِشـتـراك', callback_data='check_sub', style='primary')
    )
    edit_or_send(chat_id, message_id, text, markup)

def format_phone(phone: str) -> str:
    phone = re.sub('\\D', '', str(phone))
    if phone.startswith('213'):
        return '0' + phone[3:]
    if phone.startswith('0'):
        return phone
    return phone

def mask_phone(phone: str) -> str:
    phone = format_phone(phone)
    if len(phone) >= 10:
        return f'{phone[:4]}xxxx{phone[-2:]}'
    return phone

def format_num(phone: str) -> str:
    phone = re.sub('\\D', '', str(phone))
    if phone.startswith('213'):
        return phone
    if phone.startswith('0'):
        return '213' + phone[1:]
    return '213' + phone

def valid_phone(phone: str) -> bool:
    phone = re.sub('\\D', '', str(phone))
    return len(phone) == 10 and phone.startswith(('05', '06', '07'))

def load_registered_numbers():
    if not os.path.exists(REGISTERED_NUMBERS_FILE):
        return []
    try:
        with open(REGISTERED_NUMBERS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f'خـطـأ فـي قـراءة قـاعـدة الـبـيـانـات: {e}')
        return []

def save_registered_number(data: dict):
    numbers = load_registered_numbers()
    numbers.append(data)
    if len(numbers) > 1000:
        numbers = numbers[-1000:]
    try:
        with open(REGISTERED_NUMBERS_FILE, 'w', encoding='utf-8') as file:
            json.dump(numbers, file, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'خـطـأ فـي حـفـظ الـبـيـانـات: {e}')

def request_otp(msisdn: str) -> bool:
    cache_key = f'otp_{msisdn}'
    if cache_key in otp_cache:
        return True
    url = 'https://apim.djezzy.dz/mobile-api/oauth2/registration'
    params = {'msisdn': msisdn, 'client_id': '87pIExRhxBb3_wGsA5eSEfyATloa', 'scope': 'smsotp'}
    payload = {'consent-agreement': [{'marketing-notifications': False}], 'is-consent': True}
    try:
        response = requests.post(url, params=params, json=payload, headers=HEADERS, timeout=15)
        if response.status_code in (200, 201, 202):
            otp_cache[cache_key] = True
            return True
        logger.error(f'OTP error: {response.status_code} {response.text[:300]}')
    except Exception as e:
        logger.error(f'OTP exception: {e}')
    return False

def login_with_otp(mobile_number: str, otp: str):
    cache_key = f'token_{mobile_number}_{otp}'
    if cache_key in token_cache:
        return token_cache[cache_key]
    payload = {
        'otp': otp,
        'mobileNumber': mobile_number,
        'scope': 'djezzyAppV2',
        'client_id': '87pIExRhxBb3_wGsA5eSEfyATloa',
        'client_secret': 'uf82p68Bgisp8Yg1Uz8Pf6_v1XYa',
        'grant_type': 'mobile'
    }
    try:
        response = requests.post('https://apim.djezzy.dz/mobile-api/oauth2/token', data=payload, headers={'User-Agent': 'MobileApp/3.0.0'}, timeout=15)
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if not access_token:
                return None
            token = f'Bearer {access_token}'
            token_cache[cache_key] = token
            return token
        logger.error(f'Login error: {response.status_code} {response.text[:300]}')
    except Exception as e:
        logger.error(f'Login exception: {e}')
    return None

def activate_weekly_gift(token: str, phone: str):
    try:
        url = f'https://apim.djezzy.dz/mobile-api/api/v1/services/walk/activate-reward/{phone}'
        response = requests.post(url, json={'packageCode': OFFER_CODES['weekly']}, headers={**HEADERS, 'authorization': token}, timeout=15)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f'Weekly activation error: {e}')
        return False

def activate_product_offer(token: str, phone: str, package_code: str):
    headers = {**HEADERS, 'authorization': token}
    payload = {'packageCode': package_code}
    try:
        url1 = f'https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{phone}'
        response = requests.post(url1, json=payload, headers=headers, timeout=15)
        if response.status_code in (200, 201, 202):
            return True
        time.sleep(1)
        url2 = f'https://apim.djezzy.dz/mobile-api/api/v1/services/activate-product/{phone}'
        response = requests.post(url2, json=payload, headers=headers, timeout=15)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f'Product activation error: {e}')
        return False

def get_balance(token: str, phone: str):
    cache_key = f'balance_{phone}'
    if cache_key in balance_cache:
        return balance_cache[cache_key]
    try:
        headers = {**HEADERS, 'authorization': token}
        response_main = requests.get(f'https://apim.djezzy.dz/mobile-api/api/v1/subscribers/main-balance/{phone}', headers=headers, timeout=10)
        response_products = requests.get(f'https://apim.djezzy.dz/mobile-api/api/v1/subscribers/connected-products-balances/{phone}', headers=headers, timeout=10)
        result = {'main': None, 'bundles': [], 'subscription_name': 'غـيـر مـعـروف', 'connection_type': 'غـيـر مـعـروف'}
        if response_main.status_code == 200:
            main = response_main.json()
            result['main'] = main
            customer = main.get('data', {}).get('customerInformations', {})
            subscription = customer.get('subscriptionType', {})
            name = subscription.get('name', {})
            if isinstance(name, dict):
                result['subscription_name'] = name.get('ar') or name.get('en') or name.get('fr') or 'غـيـر مـعـروف'
            result['connection_type'] = customer.get('connectionType', 'غـيـر مـعـروف')
        if response_products.status_code == 200:
            products = response_products.json()
            data = products.get('data', {})
            result['bundles'] = data.get('products', [])
        balance_cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f'Balance error: {e}')
        return None

def format_balance_response(data):
    if not data:
        return '❌ <b>تـعـذّر جـلـب مـعـلـومـات الـرصـيـد</b>\n\nحـاول مـرّة أُخـرى بـعـد قـلـيـل.'
    try:
        main_balance = '0.00 دج'
        main = data.get('main')
        if isinstance(main, dict):
            value = main.get('data', {}).get('mainBalance')
            if value is not None:
                try:
                    main_balance = f'{float(value):.2f} دج'
                except Exception:
                    main_balance = str(value)
        text = f"💰 <b>مـعـلـومـات الـرصـيـد</b>\n💵 <b>الـرصـيـد:</b> {main_balance}\n📶 <b>نـوع الـخـط:</b> {data.get('subscription_name', 'غـيـر مـعـروف')}\n\n📦 <b>الـبـاقـات الـمـفـعـلـة</b>\n"
        bundles = data.get('bundles') or []
        if not bundles:
            text += '\n⚠️ لا تـوجـد بـاقـات مـفـعـلـة حـالـيـاً.'
        else:
            for product in bundles:
                name = 'غـيـر مـعـروف'
                commercial_name = product.get('commercialName')
                if isinstance(commercial_name, dict):
                    name = commercial_name.get('ar') or commercial_name.get('en') or commercial_name.get('fr') or 'غـيـر مـعـروف'
                elif product.get('name'):
                    product_name = product['name']
                    if isinstance(product_name, dict):
                        name = product_name.get('ar') or product_name.get('en') or product_name.get('fr') or 'غـيـر مـعـروف'
                    else:
                        name = str(product_name)
                expiry = product.get('expiryAt', 'غـيـر مـعـروف')
                if expiry != 'غـيـر مـعـروف' and len(str(expiry)) >= 10:
                    expiry = str(expiry)[:10]
                remaining = 'غـيـر مـعـروف'
                for balance in product.get('balances', []):
                    usage = str(balance.get('usageType', '')).upper()
                    if 'DATA' in usage or 'INTERNET' in usage:
                        value = balance.get('remaining', 0)
                        unit = str(balance.get('usageUnit', 'MB')).upper()
                        try:
                            value = float(value)
                            if value <= 0:
                                remaining = '0 MB'
                            elif unit == 'GB':
                                remaining = f'{value:.2f} GB'
                            elif value >= 1024:
                                remaining = f'{value / 1024:.2f} GB'
                            else:
                                remaining = f'{value:.0f} MB'
                        except Exception:
                            remaining = str(value)
                        break
                text += f'\n📦 <b>{name}</b>\n📊 <b>الـمـتـبـقـي:</b> {remaining}\n📆 <b>الـصـلاحـيـة:</b> {expiry}\n────────────────────\n'
        return text
    except Exception as e:
        logger.error(f'Balance format error: {e}')
        return '❌ <b>حـدث خـطـأ أثـنـاء مـعـالـجـة الـرصـيـد.</b>'

def build_markup(buttons, back_callback=None, show_dev=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    row = []
    for button in buttons:
        row.append(button)
        if len(row) == 2:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)

    bottom_row = []
    if back_callback:
        bottom_row.append(types.InlineKeyboardButton('🔙 رُجـوع', callback_data=back_callback, style='danger'))
    if show_dev:
        bottom_row.append(types.InlineKeyboardButton('👨‍💻 الـمـطـوِّر', url=DEVELOPER_URL, style='primary'))
    
    if bottom_row:
        markup.row(*bottom_row)

    return markup

def edit_or_send(chat_id, message_id, text, markup=None):
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    bot.clear_step_handler_by_chat_id(chat_id)

    # التحقق من الاشتراك الإجباري
    if not check_user_subscription(user_id):
        send_force_subscription_message(chat_id)
        return

    # إذا كان المستخدم يسجل دخوله بالفعل، نقوم بعرض القائمة الرئيسية مباشرة
    if chat_id in user_sessions:
        session = user_sessions[chat_id]
        balance = get_balance(session['token'], session['phone'])
        sub_name = balance.get('subscription_name', 'غـيـر مـعـروف') if balance else 'غـيـر مـعـروف'
        show_main_menu(chat_id, session['display_phone'], sub_name)
        return

    # إذا لم يكن مسجلاً، نقوم إرسال الرسالة الترحيبية ثم الطلب
    start_by_chat(chat_id)

def start_by_chat(chat_id):
    bot.clear_step_handler_by_chat_id(chat_id)
    user_sessions.pop(chat_id, None)
    user_numbers.pop(chat_id, None)
    pending_otp_resend.pop(chat_id, None)

    # الرسالة الأولى: الترحيب وشرح الاستخدام
    msg1 = (
        "🚀 <b>أهـلاً وسـهـلاً بـك</b> \n"
        "<b>𝐨𝐜𝐭𝐢𝐧𝐞𝐭 𝐛𝐨𝐭 🤖</b>\n\n\n"
        "📱 <b>طـريـقـة الاسـتـخـدام:</b>\n\n"
        "1️⃣ أرسـل رَقـم جـيـزي الـخـاص بـك.\n"
        "2️⃣ أَدخـل رمـز الـتـحـقـق الـمـرسـل عـبـر SMS.\n"
        "3️⃣ اَخـتـر الـخـدمـة أو الـعـرض الـمـنـاسـب.\n"
        "4️⃣ تـابـع الـنـتـيـجـة مـبـاشـرة."
    )
    bot.send_message(chat_id, msg1, parse_mode='HTML')

    # الرسالة الثانية المنفصلة: طلب إرسال الرقم فقط
    msg2 = "📲 <b>أرسـل رَقـم هـاتـفـك الآن لـلـبـدء</b>"
    msg = bot.send_message(chat_id, msg2, parse_mode='HTML')
    bot.register_next_step_handler(msg, handle_phone_text)

def handle_phone_text(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text and message.text.startswith('/'):
        bot.clear_step_handler_by_chat_id(chat_id)
        if message.text.strip() == '/start':
            start(message)
        return

    if not check_user_subscription(user_id):
        send_force_subscription_message(chat_id)
        return

    phone = re.sub('\\D', '', message.text or '')
    if not valid_phone(phone):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔄 الـمـحـاوَلـة مـرّة أُخـرى', callback_data='retry_phone', style='primary'))
        bot.send_message(chat_id, '❌ <b>رَقـم غـيـر صـحـيـح</b>\n\n📱 أرسـل رَقـم جـيـزي صـحـيـحـاً مـثـل:\n<code>0770123456</code>', parse_mode='HTML', reply_markup=markup)
        return
    process_phone_input(message, phone)

def process_phone_input(message, phone):
    chat_id = message.chat.id
    formatted = format_num(phone)
    display = format_phone(phone)
    user_numbers[chat_id] = {'original': phone, 'formatted': formatted, 'display': display}
    pending_otp_resend[chat_id] = {'formatted_phone': formatted}
    status = bot.send_message(chat_id, '✅ 📲 <b>جـاري إرسـال رمـز الـتـحـقـق...</b>')
    future = executor.submit(request_otp, formatted)
    try:
        success = future.result(timeout=20)
    except Exception:
        success = False
    if not success:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔄 إعـادة الـمـحـاوَلـة', callback_data='retry_phone', style='primary'))
        try:
            bot.edit_message_text('✅ ❌ <b>تـعـذّر إرسـال رمـز الـتـحـقـق.</b>\n\nتـأكـد مـن أن الـرَقـم صـحـيـح وحـاول مـرّة أُخـرى.', chat_id, status.message_id, parse_mode='HTML', reply_markup=markup)
        except Exception:
            pass
        user_numbers.pop(chat_id, None)
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('🔄 إعـادة إرسـال', callback_data='resend_otp', style='primary'),
        types.InlineKeyboardButton('❌ إلـغـاء', callback_data='cancel_operation', style='danger')
    )
    try:
        bot.edit_message_text('✅ 📩 <b>تـم إرسـال رمـز الـتـحـقـق</b>\n\n🔐 أَدخـل الـرمـز الـمـرسـل إﻟـى هـاتـفـك.\nعـادةً يـتـكـون الـرمـز مـن 6 أرْقـام.', chat_id, status.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception:
        pass
    bot.register_next_step_handler(status, process_otp)

def resend_otp_code(chat_id, callback_id):
    data = pending_otp_resend.get(chat_id)
    if not data:
        bot.answer_callback_query(callback_id, '❌ انـتـهـت الـجـلـسـة.', show_alert=True)
        return
    bot.answer_callback_query(callback_id, '📲 جـاري إرسـال رمـز جـديـد...')
    status = bot.send_message(chat_id, '📲 <b>جـاري إعـادة إرسـال الـرمـز...</b>')
    future = executor.submit(request_otp, data['formatted_phone'])
    try:
        success = future.result(timeout=20)
    except Exception:
        success = False
    if success:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('🔄 إعـادة إرسـال', callback_data='resend_otp', style='primary'),
            types.InlineKeyboardButton('❌ إلـغـاء', callback_data='cancel_operation', style='danger')
        )
        bot.edit_message_text('📩 <b>تـم إرسـال رمـز جـديـد</b>\n\n🔐 أَدخـل الـرمـز الـمـرسـل إﻟـيـك.', chat_id, status.message_id, parse_mode='HTML', reply_markup=markup)
        bot.register_next_step_handler(status, process_otp)
    else:
        bot.edit_message_text('❌ <b>فـشـل إرسـال الـرمـز.</b>\n\nحـاول مـرّة أُخـرى بـعـد قـلـيـل.', chat_id, status.message_id, parse_mode='HTML')

def process_otp(message):
    chat_id = message.chat.id
    if not message.text:
        return
    if message.text.startswith('/'):
        bot.clear_step_handler_by_chat_id(chat_id)
        if message.text.strip() == '/start':
            start(message)
        return
    otp = message.text.strip()
    if chat_id not in user_numbers:
        bot.send_message(chat_id, '✅ ❌ <b>انـتـهـت جـلـسـة الـتـحـقـق.</b>\n\nاسـتـخـدم /start لـلـبـدء مـن جـديـد.')
        return
    if not otp.isdigit() or not 4 <= len(otp) <= 8:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('🔄 إعـادة إرسـال', callback_data='resend_otp', style='primary'),
            types.InlineKeyboardButton('❌ إلـغـاء', callback_data='cancel_operation', style='danger')
        )
        bot.send_message(chat_id, '✅ ❌ <b>رمـز غـيـر صـحـيـح</b>\n\n🔐 أَدخـل رمـز الـتـحـقـق بـشـكـل صـحـيـح.', reply_markup=markup)
        bot.register_next_step_handler(message, process_otp)
        return

    phone_data = user_numbers[chat_id]
    status = bot.send_message(chat_id, '✅ 🔐 <b>جـاري الـتـحـقـق مـن الـرمـز...</b>')
    token = login_with_otp(phone_data['formatted'], otp)

    if not token:
        try:
            bot.delete_message(chat_id, status.message_id)
        except Exception:
            pass
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('🔄 إعـادة الـمـحـاوَلـة', callback_data='resend_otp', style='primary'),
            types.InlineKeyboardButton('❌ إلـغـاء', callback_data='cancel_operation', style='danger')
        )
        bot.send_message(chat_id, '✅ ❌ <b>رمـز الـتـحـقـق غـيـر صـحـيـح</b>\n\nتـحـقـق مـن الـرمـز وحـاول مـرّة أُخـرى.', reply_markup=markup)
        bot.register_next_step_handler(message, process_otp)
        return

    user = message.from_user
    user_sessions[chat_id] = {
        'phone': phone_data['formatted'],
        'display_phone': phone_data['display'],
        'token': token,
        'username': f'@{user.username}' if user.username else 'لا يـوجـد',
        'full_name': user.full_name or 'غـيـر مـعـروف',
        'user_id': user.id,
        'last_activity': time.time()
    }
    user_numbers.pop(chat_id, None)
    pending_otp_resend.pop(chat_id, None)

    # تحديث نص رسالة الانتظار مباشرة للبقاء ظاهراً
    try:
        bot.edit_message_text('⏳ <b>جـاري جـلـب مـعـلـومـات الـحـسـاب...</b>', chat_id, status.message_id, parse_mode='HTML')
    except Exception:
        pass

    # جلب تفاصيل الرصيد
    balance = get_balance(token, phone_data['formatted'])
    subscription = balance.get('subscription_name', 'غـيـر مـعـروف') if balance else 'غـيـر مـعـروف'

    # تحويل رسالة الانتظار مباشرة إلى قائمة العروض بدون اختفاء
    show_main_menu(chat_id, phone_data['display'], subscription, message_id=status.message_id)

def show_main_menu(chat_id, display_phone, subscription_name='غـيـر مـعـروف', message_id=None):
    session = user_sessions.get(chat_id)
    if not session:
        start_by_chat(chat_id)
        return
    session['last_activity'] = time.time()
    
    buttons = [
        types.InlineKeyboardButton('👑 IMTIYAZ', callback_data='menu_imtiyaz', style='primary'),
        types.InlineKeyboardButton('📦 DJEZZY IZZY', callback_data='menu_izzy', style='primary'),
        types.InlineKeyboardButton('⚡ DJEZZY ZID', callback_data='menu_zid', style='primary'),
        types.InlineKeyboardButton('🔥 HAYLA BEZZEF', callback_data='menu_hayla_bezzef', style='primary'),
        types.InlineKeyboardButton('🌟 HAYLA MAXI', callback_data='menu_hayla_maxi', style='primary'),
        types.InlineKeyboardButton('🎁 العـروض الـمـجـانـيـة', callback_data='menu_free', style='primary'),
        types.InlineKeyboardButton('💰 رصـيـدي', callback_data='check_balance', style='primary'),
        types.InlineKeyboardButton('🚪 تـسـجـيـل خـروج', callback_data='logout', style='danger')
    ]
    markup = build_markup(buttons, show_dev=True)
    text = f'📋 ╔════════════════════╗\n      🤖 <b>قـائـمـة الـخـدمـات</b>\n╚════════════════════╝\n\n📱 <b>الـرَّقـم:</b> <code>{display_phone}</code>\n📶 <b>نـوع الـخـط:</b> {subscription_name}\n\nاِخـتـر الـخـدمـة أو الـعـرض الـمـنـاسـب:'
    edit_or_send(chat_id, message_id, text, markup)

def handle_category_menu(chat_id, category_type, message_id=None):
    session = user_sessions.get(chat_id)
    if not session:
        start_by_chat(chat_id)
        return
    
    category_data = {
        'imtiyaz': (IMTIYAZ_OFFERS, '👑 <b>عـروض امتـيـاز (IMTIYAZ)</b>\n\nاخـتـر الـعـرض الـمـنـاسـب:'),
        'izzy': (IZZY_OFFERS, '📦 <b>عـروض جـيـزي إيـزي (DJEZZY IZZY)</b>\n\nاخـتـر الـعـرض الـمـنـاسـب:'),
        'zid': (ZID_OFFERS, '⚡ <b>عـروض جـيـزي زيـد (DJEZZY ZID)</b>\n\nاخـتـر الـعـرض الـمـنـاسـب:'),
        'hayla_bezzef': (HAYLA_BEZZEF_OFFERS, '🔥 <b>عـروض هـايـلـة بـزاف (HAYLA BEZZEF)</b>\n\nاخـتـر الـعـرض الـمـنـاسـب:'),
        'hayla_maxi': (HAYLA_MAXI_OFFERS, '🌟 <b>عـروض هـايـلـة مـاكـسـي (HAYLA MAXI)</b>\n\nاخـتـر الـعـرض الـمـنـاسـب:'),
        'free': (FREE_OFFERS, '🎁 <b>العـروض الـمـجـانـيـة</b>\n\nاخـتـر الـعـرض الـمـجـانـي:')
    }
    
    if category_type not in category_data:
        return
        
    offers, text = category_data[category_type]
    buttons = [
        types.InlineKeyboardButton(offer['button_text'], callback_data=f'view_offer_{offer_id}', style='primary')
        for offer_id, offer in offers.items()
    ]
    markup = build_markup(buttons, back_callback='back_to_main', show_dev=True)
    edit_or_send(chat_id, message_id, text, markup)

def show_offer_details(chat_id, offer_id, message_id=None):
    session = user_sessions.get(chat_id)
    if not session:
        start_by_chat(chat_id)
        return
    offer = ALL_OFFERS.get(offer_id)
    if not offer:
        bot.send_message(chat_id, '❌ <b>العـرض غـيـر مـتـوفـر.</b>')
        return
    back_target = f"menu_{offer.get('type', 'main')}"
    if offer.get('category') == 'free':
        back_target = 'menu_free'
    text = (
        f"{offer['emoji']} <b>تـفـاصـيـل العـرض</b>\n\n"
        f"<b>الاسـم:</b> {offer['name']}\n"
        f"<b>الـسـعـر:</b> {offer['price']}\n"
        f"<b>الـصـلاحـيـة:</b> {offer['duration']}\n"
        f"<b>الـمـمـيـزات:</b>\n{offer['description']}\n\n"
        f"⚡ <b>هـل تـريـد تـفـعـيـل هـذا العـرض الآن؟</b>"
    )
    buttons = [
        types.InlineKeyboardButton('✅ تـفـعـيـل الآن', callback_data=f'activate_confirm_{offer_id}', style='primary'),
        types.InlineKeyboardButton('🔙 رُجـوع', callback_data=back_target, style='danger')
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    edit_or_send(chat_id, message_id, text, markup)

def process_offer_activation(chat_id, offer_id, message_id=None):
    if chat_id in processing_users:
        bot.send_message(chat_id, '⏳ <b>جـاري مـعـالـجـة طـلـب سـابـق...</b>\n\nيـرجـى الاِنـتـظـار.')
        return
    session = user_sessions.get(chat_id)
    if not session:
        start_by_chat(chat_id)
        return
    offer = ALL_OFFERS.get(offer_id)
    if not offer:
        bot.send_message(chat_id, '❌ <b>العـرض غـيـر مـتـوفـر.</b>')
        return
    processing_users.add(chat_id)
    status_text = f"⏳ <b>جـاري تـفـعـيـل عرض: {offer['name']}...</b>\n\nيـرجـى الاِنـتـظـار قـلـيـلاً."
    if message_id:
        try:
            bot.edit_message_text(status_text, chat_id, message_id, parse_mode='HTML')
            status_msg_id = message_id
        except Exception:
            status_msg = bot.send_message(chat_id, status_text)
            status_msg_id = status_msg.message_id
    else:
        status_msg = bot.send_message(chat_id, status_text)
        status_msg_id = status_msg.message_id

    token = session['token']
    phone = session['phone']
    success = False
    
    if offer_id == 'weekly':
        success = activate_weekly_gift(token, phone)
    else:
        success = activate_product_offer(token, phone, offer['code'])
        
    processing_users.remove(chat_id)
    back_target = f"menu_{offer.get('type', 'main')}"
    if offer.get('category') == 'free':
        back_target = 'menu_free'
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('🔙 العـودة للـقـائـمـة', callback_data=back_target, style='primary'),
        types.InlineKeyboardButton('🔝 الـقـائـمـة الـرئـيـسـيـة', callback_data='back_to_main', style='primary')
    )
    if success:
        save_registered_number({
            'phone': phone,
            'user_id': session['user_id'],
            'full_name': session['full_name'],
            'username': session['username'],
            'activated_offer': offer['name'],
            'offer_id': offer_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        text = f"✅ <b>تـم تـفـعـيـل العـرض بـنـجـاح!</b>\n\n<b>العـرض:</b> {offer['name']}\n📱 <b>الـرَّقـم:</b> <code>{session['display_phone']}</code>\n\nتـم تـثـبـيـت العـرض عـلـى شـريـحـتـك."
        try:
            amount = offer.get('amount', offer.get('display_name', 'غير معروف'))

            group_msg = (
                f"✅ <b>تم تفعيل {amount} ✅</b>\n"
                f"👤الاسم: {session['full_name']}\n"
                f"🆔اللايدي: <code>{session['user_id']}</code>\n"
                f"📇اليوزر: {session['username']}\n"
                f"🕓الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📦الكمية: {amount}"
            )

            bot.send_message(
                ACTIVATION_GROUP,
                group_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f'Group log error: {e}')
    else:
        text = f"❌ <b>فـشـل تـفـعـيـل العـرض</b>\n\n<b>العـرض:</b> {offer['name']}\n\nقد يـكـون الـرصـيـد غـيـر كـافٍ، أو أن العـرض غـيـر مـتـافـق مـع شـريـحـتـك."
    edit_or_send(chat_id, status_msg_id, text, markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    
    if data == 'check_sub':
        if check_user_subscription(call.from_user.id):
            bot.answer_callback_query(call.id, '✅ تـم تـأكـيـد الاِشـتـراك بـنـجـاح!')
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
            if chat_id in user_sessions:
                session = user_sessions[chat_id]
                balance = get_balance(session['token'], session['phone'])
                sub_name = balance.get('subscription_name', 'غـيـر مـعـروف') if balance else 'غـيـر مـعـروف'
                show_main_menu(chat_id, session['display_phone'], sub_name)
            else:
                start_by_chat(chat_id)
        else:
            bot.answer_callback_query(call.id, '❌ لـم تـشـتـرك فـي الـقـنـاة بـعـد!', show_alert=True)
        return

    if not check_user_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, '⚠️ يـجـب الاِشـتـراك فـي الـقـنـاة أوَّلاً!', show_alert=True)
        send_force_subscription_message(chat_id, message_id)
        return

    if data == 'retry_phone':
        bot.answer_callback_query(call.id)
        start_by_chat(chat_id)
        return
    if data == 'resend_otp':
        resend_otp_code(chat_id, call.id)
        return
    if data == 'cancel_operation':
        bot.answer_callback_query(call.id, 'تـم الإلـغـاء.')
        user_sessions.pop(chat_id, None)
        user_numbers.pop(chat_id, None)
        pending_otp_resend.pop(chat_id, None)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        start_by_chat(chat_id)
        return

    if data == 'logout':
        bot.answer_callback_query(call.id, '🚪 تم تسجيل الخروج بنجاح')
        user_sessions.pop(chat_id, None)
        user_numbers.pop(chat_id, None)
        pending_otp_resend.pop(chat_id, None)
        bot.clear_step_handler_by_chat_id(chat_id)
        
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        start_by_chat(chat_id)
        return

    session = user_sessions.get(chat_id)
    if not session:
        bot.answer_callback_query(call.id, '⚠️ انـتـهـت الـجـلـسـة، يـرجـى إعـادة الـتـسـجـيـل.', show_alert=True)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        start_by_chat(chat_id)
        return

    bot.answer_callback_query(call.id)
    
    if data == 'back_to_main':
        balance = get_balance(session['token'], session['phone'])
        sub_name = balance.get('subscription_name', 'غـيـر مـعـروف') if balance else 'غـيـر مـعـروف'
        show_main_menu(chat_id, session['display_phone'], sub_name, message_id)
    elif data.startswith('menu_'):
        category = data.replace('menu_', '')
        handle_category_menu(chat_id, category, message_id)
    elif data.startswith('view_offer_'):
        offer_id = data.replace('view_offer_', '')
        show_offer_details(chat_id, offer_id, message_id)
    elif data.startswith('activate_confirm_'):
        offer_id = data.replace('activate_confirm_', '')
        process_offer_activation(chat_id, offer_id, message_id)
    elif data == 'check_balance':
        show_user_balance(chat_id, message_id)

def show_user_balance(chat_id, message_id=None):
    session = user_sessions.get(chat_id)
    if not session:
        start_by_chat(chat_id)
        return
    status_msg = bot.send_message(chat_id, '⏳ <b>جـاري جـلـب مـعـلـومـات الـرصـيـد...</b>')
    balance = get_balance(session['token'], session['phone'])
    text = format_balance_response(balance)
    try:
        bot.delete_message(chat_id, status_msg.message_id)
    except Exception:
        pass
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('🔄 تـحـديـث', callback_data='check_balance', style='primary'),
        types.InlineKeyboardButton('🔙 العـودة للـقـائـمـة', callback_data='back_to_main', style='danger')
    )
    edit_or_send(chat_id, message_id, text, markup)

def cleanup_sessions():
    while True:
        try:
            now = time.time()
            expired = [cid for cid, s in user_sessions.items() if now - s.get('last_activity', 0) > 86400]
            for cid in expired:
                user_sessions.pop(cid, None)
                user_numbers.pop(cid, None)
                pending_otp_resend.pop(cid, None)
        except Exception as e:
            logger.error(f'Session cleanup error: {e}')
        time.sleep(3600)

cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    logger.info('🚀 NexsBot starting up...')
    try:
        bot.remove_webhook()
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30, skip_pending=True)
        except Exception as e:
            logger.error(f'Bot polling crashed: {e}')
            time.sleep(3)
ن
