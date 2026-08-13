import json
import logging
import re
import requests
import os
from flask import current_app, jsonify

# Load interactive menus from JSON
MENUS_FILE = os.path.join(os.path.dirname(__file__), '../../whatsapp_interactive_menus.json')
try:
    with open(MENUS_FILE, 'r', encoding='utf-8') as f:
        INTERACTIVE_MENUS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    INTERACTIVE_MENUS = {}
    logging.warning(f"Could not load interactive menus from {MENUS_FILE}")


LANGUAGE_BUTTONS = [
    {"type": "reply", "reply": {"id": "lang_urdu", "title": "اردو"}},
    {"type": "reply", "reply": {"id": "lang_pashto", "title": "پښتو"}},
    {"type": "reply", "reply": {"id": "lang_english", "title": "English"}},
]


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def get_interactive_button_input(recipient, header_text, body_text, buttons):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"type": "text", "text": header_text},
                "body": {"text": body_text},
                "action": {"buttons": buttons},
            },
        }
    )


def get_interactive_list_input(
    recipient,
    body_text,
    button_text,
    sections,
    header_text=None,
    footer_text=None,
):
    interactive_payload = {
        "type": "list",
        "body": {"text": body_text},
        "action": {"button": button_text, "sections": sections},
    }

    if header_text:
        interactive_payload["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive_payload["footer"] = {"text": footer_text}

    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": interactive_payload,
        }
    )


def parse_incoming_whatsapp_message(message):
    if "interactive" in message:
        interactive = message["interactive"]
        if interactive.get("type") == "button_reply":
            return interactive["button_reply"].get("id") or interactive["button_reply"].get("title", "").strip()
        if interactive.get("type") == "list_reply":
            return interactive["list_reply"].get("id") or interactive["list_reply"].get("title", "").strip()
    if "text" in message:
        return message["text"]["body"].strip()
    return None


def get_language_selection_payload(recipient):
    # Try to use menu from JSON, fallback to hardcoded
    if INTERACTIVE_MENUS and 'language_selection_menu' in INTERACTIVE_MENUS:
        menu = INTERACTIVE_MENUS['language_selection_menu'].copy()
        menu['to'] = recipient  # Replace template with actual recipient
        # Ensure encoding is correct
        try:
            return json.dumps(menu, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error encoding menu to JSON: {e}")
    
    # Fallback to original method
    return get_interactive_button_input(
        recipient,
        "Darul Eman Wal Taqwa",
        "برائے مہربانی اپنی زبان کا انتخاب کریں:\nPlease select your language:",
        LANGUAGE_BUTTONS,
    )


def get_response_from_json(language, option_id):
    """Get response message from JSON file based on language and option ID"""
    if not INTERACTIVE_MENUS or 'responses_data' not in INTERACTIVE_MENUS:
        return None
    
    responses_data = INTERACTIVE_MENUS['responses_data']
    
    # Extract option number (e.g., "opt_1" from "opt_1_ur")
    option_key = None
    if option_id:
        # Handle formats like "opt_1", "opt_1_ur", "opt_1_en"
        parts = option_id.split('_')
        if parts[0] == 'opt' and len(parts) >= 2:
            option_key = f"opt_{parts[1]}"
    
    if option_key and option_key in responses_data:
        lang_map = {'ur': 'urdu', 'ps': 'pashto', 'en': 'english'}
        lang_key = lang_map.get(language, 'english')
        
        if lang_key in responses_data[option_key]:
            return responses_data[option_key][lang_key]
    
    return None


def get_localized_menu_payload(recipient, language):
    # Try to get menu from JSON file first
    if INTERACTIVE_MENUS:
        lang_menu_key = None
        if language == "ur":
            lang_menu_key = 'urdu_main_menu'
        elif language == "ps":
            lang_menu_key = 'pashto_main_menu'
        else:
            lang_menu_key = 'english_main_menu'
        
        if lang_menu_key in INTERACTIVE_MENUS:
            menu = INTERACTIVE_MENUS[lang_menu_key].copy()
            menu['to'] = recipient
            try:
                payload = json.dumps(menu, ensure_ascii=False)
                logging.info(f"Using menu from JSON for language: {language}")
                return payload
            except Exception as e:
                logging.error(f"Error encoding {lang_menu_key} to JSON: {e}")
    
    # Fallback to original hardcoded method
    logging.info(f"Using fallback hardcoded menu for language: {language}")
    if language == "ur":
        body_text = "محترم صارف! خوش آمدید۔ آپ کی رہنمائی کے لیے درج ذیل معلومات دستیاب ہیں۔ برائے مہربانی مطلوبہ آپشن کا انتخاب کریں۔"
        button_text = "فہرست دیکھیں"
        header_text = "دارالایمان والتقویٰ"
        sections = [
            {
                "title": "مرکزی مینو",
                "rows": [
                    {"id": "opt_1_ur", "title": "واٹس ایپ گروپ", "description": "گروپ کا لنک حاصل کریں"},
                    {"id": "opt_2_ur", "title": "رابطہ مرکز", "description": "مرکز کربوغہ شریف سے رابطہ کریں"},
                    {"id": "opt_3_ur", "title": "جامعہ زکریا", "description": "جامعہ زکریا کربوغہ شریف کی معلومات"},
                    {"id": "opt_4_ur", "title": "مکاتب قرآنیہ", "description": "مکاتب قرآنیہ سے رابطہ کریں"},
                    {"id": "opt_5_ur", "title": "مالی اعانت", "description": "بینک اکاؤنٹ نمبر حاصل کریں"},
                    {"id": "opt_6_ur", "title": "ذیلی مراکز", "description": "پشاور، مندرہ، اسلام آباد، بنوں"},
                    {"id": "opt_7_ur", "title": "آنے والے اجتماعات", "description": "اجتماعات کی معلومات حاصل کریں"},
                    {"id": "opt_0_ur", "title": "نمائندہ سے بات", "description": "نمائندہ سے رابطہ کریں"},
                ],
            }
        ]
    elif language == "ps":
        body_text = "قدرمن ملګری! پخیر راغلئ. د خپلې اړتیا مطابق لاندې انتخاب وټاکئ."
        button_text = "فهرست وګورئ"
        header_text = "دارالایمان والتقویٰ"
        sections = [
            {
                "title": "اصلي مینو",
                "rows": [
                    {"id": "opt_1_ps", "title": "واټس اپ ګروپ", "description": "د واټس اپ ګروپ لینک ترلاسه کړئ"},
                    {"id": "opt_2_ps", "title": "ارتباطي مرکز", "description": "د کربوغې شریف مرکز سره ارتباط"},
                    {"id": "opt_3_ps", "title": "جامعه زکریا", "description": "د جامعه زکریا کربوغې شریف معلومات"},
                    {"id": "opt_4_ps", "title": "مکاتب قرآنیه", "description": "د قرآني مکاتبو سره د رابطې لپاره"},
                    {"id": "opt_5_ps", "title": "مالي مرسته", "description": "د بنک اکاونټ شمیره ترلاسه کړئ"},
                    {"id": "opt_6_ps", "title": "فرعي مرکزونه", "description": "پېښور، مندره، اسلام اباد، بنو"},
                    {"id": "opt_7_ps", "title": "راتلونکي اجتماعات", "description": "د راتلونکو اجتماعاتو معلومات"},
                    {"id": "opt_0_ps", "title": "استازي سره خبرې", "description": "د استازي (ایجنټ) سره د رابطې لپاره"},
                ],
            }
        ]
    else:
        body_text = "Welcome! Please select an option from the menu below to proceed."
        button_text = "View Menu"
        header_text = "Darul Eman Wal Taqwa"
        sections = [
            {
                "title": "Main Menu",
                "rows": [
                    {"id": "opt_1_en", "title": "WhatsApp Group", "description": "Get WhatsApp Group link"},
                    {"id": "opt_2_en", "title": "Contact Center", "description": "Contact Karbogha Sharif Center"},
                    {"id": "opt_3_en", "title": "Jamia Zakariya", "description": "Info about Jamia Zakariya"},
                    {"id": "opt_4_en", "title": "Quranic Academies", "description": "Contact Quranic Academies"},
                    {"id": "opt_5_en", "title": "Financial Support", "description": "Get bank account details"},
                    {"id": "opt_6_en", "title": "Sub-Centers", "description": "Peshawar, Mandra, Islamabad, Bannu"},
                    {"id": "opt_7_en", "title": "Upcoming Events", "description": "Information on upcoming gatherings"},
                    {"id": "opt_0_en", "title": "Talk to Representative", "description": "Connect with a live representative"},
                ],
            }
        ]

    return get_interactive_list_input(recipient, body_text, button_text, sections, header_text=header_text)


def get_demo_response_text(language, option_id):
    """First tries to get response from JSON file, then falls back to demo messages"""
    # Try JSON file first
    json_response = get_response_from_json(language, option_id)
    if json_response:
        return json_response
    
    # Fallback to demo messages
    option_key = ""
    if option_id:
        parts = option_id.split("_")
        if len(parts) >= 2 and parts[0] in {"opt", "city"}:
            option_key = parts[1]
        elif len(parts) >= 2:
            option_key = parts[1]
        elif option_id.isdigit():
            option_key = option_id
    demo_messages = {
        "1": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ واٹس ایپ گروپ کا لنک جلدی ہی شیئر کیا جائے گا۔",
            "ps": "دا دیمو پوستنه ده. د واټس اپ ګروپ لینک به ژر شریک شي.",
            "en": "This is a demo response. The WhatsApp group link will be shared soon.",
        },
        "2": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ رابطہ مرکز کی معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د ارتباطي مرکز معلومات به ژر چمتو شي.",
            "en": "This is a demo response. Contact center details will be shared soon.",
        },
        "3": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ جامعہ زکریا سے متعلق معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د جامعه زکریا معلومات به ژر چمتو شي.",
            "en": "This is a demo response. Information about Jamia Zakariya will be shared soon.",
        },
        "4": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ مکاتب قرآنیہ کے لیے رابطہ معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د قرآني مکاتب لپاره د ارتباط معلومات به ژر چمتو شي.",
            "en": "This is a demo response. Contact details for the Quranic academies will be shared soon.",
        },
        "5": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ مالی اعانت کے لیے بینک تفصیلات جلدی ہی جاری کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د مالي مرسته لپاره د بانک تفصیلات به ژر چمتو شي.",
            "en": "This is a demo response. Bank details for financial support will be shared soon.",
        },
        "6": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ ذیلی مراکز کے بارے میں معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د فرعي مرکزونو معلومات به ژر چمتو شي.",
            "en": "This is a demo response. Details about the sub-centers will be shared soon.",
        },
        "7": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ آنے والے اجتماعات کی تفصیلات جلدی ہی شیئر کی جائیں گی۔",
            "ps": "دا دیمو پوستنه ده. د راتلونکو اجتماعاتو تفصیلات به ژر شریک شي.",
            "en": "This is a demo response. Upcoming event details will be shared soon.",
        },
        "0": {
            "ur": "یہ ایک ڈیمو جواب ہے۔ نمائندہ سے رابطہ کرنے والی معلومات جلدی ہی بھیجی جائے گی۔",
            "ps": "دا دیمو پوستنه ده. د استازي سره د اړیکې معلومات به ژر واستول شي.",
            "en": "This is a demo response. Representative contact information will be shared soon.",
        },
    }

    lang = "en"
    if language in {"ur", "ps", "en"}:
        lang = language

    if option_key in demo_messages:
        return demo_messages[option_key][lang]

    return demo_messages["1"][lang]


def get_sub_centers_menu_payload(recipient, language):
    if language == "ur":
        body_text = "برائے مہربانی اپنے شہر کا انتخاب کریں۔"
        button_text = "شہر منتخب کریں"
        header_text = "ذیلی مراکز"
        sections = [
            {
                "title": "شہروں کی فہرست",
                "rows": [
                    {"id": "city_peshawar_ur", "title": "پشاور", "description": "پشاور کے ذیلی مرکز کی معلومات"},
                    {"id": "city_mandra_ur", "title": "مندرہ", "description": "مندرہ کے ذیلی مرکز کی معلومات"},
                    {"id": "city_islamabad_ur", "title": "اسلام آباد", "description": "اسلام آباد کے ذیلی مرکز کی معلومات"},
                    {"id": "city_bannu_ur", "title": "بنوں", "description": "بنوں کے ذیلی مرکز کی معلومات"},
                ],
            }
        ]
    elif language == "ps":
        body_text = "مهرباني د خپل ښار انتخاب وکړئ."
        button_text = "ښار وټاکئ"
        header_text = "فرعي مرکزونه"
        sections = [
            {
                "title": "د ښارونو لیست",
                "rows": [
                    {"id": "city_peshawar_ps", "title": "پېښور", "description": "د پېښور فرعي مرکز معلومات"},
                    {"id": "city_mandra_ps", "title": "مندره", "description": "د مندره فرعي مرکز معلومات"},
                    {"id": "city_islamabad_ps", "title": "اسلام اباد", "description": "د اسلام اباد فرعي مرکز معلومات"},
                    {"id": "city_bannu_ps", "title": "بنو", "description": "د بنو فرعي مرکز معلومات"},
                ],
            }
        ]
    else:
        body_text = "Please select your city."
        button_text = "Select City"
        header_text = "Sub-Centers"
        sections = [
            {
                "title": "Cities",
                "rows": [
                    {"id": "city_peshawar_en", "title": "Peshawar", "description": "Details for Peshawar sub-center"},
                    {"id": "city_mandra_en", "title": "Mandra", "description": "Details for Mandra sub-center"},
                    {"id": "city_islamabad_en", "title": "Islamabad", "description": "Details for Islamabad sub-center"},
                    {"id": "city_bannu_en", "title": "Bannu", "description": "Details for Bannu sub-center"},
                ],
            }
        ]

    return get_interactive_list_input(recipient, body_text, button_text, sections, header_text=header_text)


def get_city_response_text(language, option_id):
    city = ""
    if option_id:
        parts = option_id.split("_")
        if len(parts) >= 2:
            city = parts[1]
    city_messages = {
        "peshawar": {
            "ur": "پشاور کے ذیلی مرکز کے بارے میں معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "د پېښور فرعي مرکز معلومات به ژر چمتو شي.",
            "en": "Details for the Peshawar sub-center will be shared soon.",
        },
        "mandra": {
            "ur": "مندرہ کے ذیلی مرکز کے بارے میں معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "د مندره فرعي مرکز معلومات به ژر چمتو شي.",
            "en": "Details for the Mandra sub-center will be shared soon.",
        },
        "islamabad": {
            "ur": "اسلام آباد کے ذیلی مرکز کے بارے میں معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "د اسلام اباد فرعي مرکز معلومات به ژر چمتو شي.",
            "en": "Details for the Islamabad sub-center will be shared soon.",
        },
        "bannu": {
            "ur": "بنوں کے ذیلی مرکز کے بارے میں معلومات جلدی ہی فراہم کی جائیں گی۔",
            "ps": "د بنو فرعي مرکز معلومات به ژر چمتو شي.",
            "en": "Details for the Bannu sub-center will be shared soon.",
        },
    }

    lang = "en"
    if language in {"ur", "ps", "en"}:
        lang = language

    return city_messages.get(city, city_messages["peshawar"])[lang]


def build_menu_payload(recipient, selected_option=None):
    if not selected_option:
        return get_language_selection_payload(recipient)

    option = selected_option.strip().lower()

    if option in {"lang_urdu", "lang_pashto", "lang_english"}:
        language = "ur" if option == "lang_urdu" else "ps" if option == "lang_pashto" else "en"
        return get_localized_menu_payload(recipient, language)

    if option.startswith("city_"):
        language = "en"
        if option.endswith("_ur"):
            language = "ur"
        elif option.endswith("_ps"):
            language = "ps"
        return get_text_message_input(recipient, get_city_response_text(language, option))

    if option.startswith("opt_"):
        language = "en"
        if option.endswith("_ur"):
            language = "ur"
        elif option.endswith("_ps"):
            language = "ps"
        return get_text_message_input(recipient, get_demo_response_text(language, option))

    return get_language_selection_payload(recipient)


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        # Parse JSON string to dict, then let requests handle JSON encoding
        payload = json.loads(data) if isinstance(data, str) else data
        logging.info(f"Sending payload to Facebook: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        # Log the detailed error response from Facebook
        error_msg = f"Request failed due to: {e}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logging.error(f"{error_msg}. Facebook API response: {json.dumps(error_detail, ensure_ascii=False)}")
            except:
                logging.error(f"{error_msg}. Response body: {e.response.text}")
        else:
            logging.error(error_msg)
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    return whatsapp_style_text


def process_whatsapp_message(body):
    try:
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to extract message data from webhook body: {e}")
        return

    selected_option = parse_incoming_whatsapp_message(message)
    if selected_option is None:
        logging.info("Unsupported incoming WhatsApp message type; no response sent.")
        return

    logging.info(f"Processing message from {wa_id}: {selected_option}")
    payload = build_menu_payload(wa_id, selected_option)
    send_message(payload)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    if not (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    ):
        return False

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    return message.get("type") in {"text", "interactive"}
