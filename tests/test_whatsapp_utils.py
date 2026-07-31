import json
import unittest

from app.utils.whatsapp_utils import (
    get_demo_response_text,
    get_language_selection_payload,
    get_localized_menu_payload,
)


class WhatsAppUtilsTests(unittest.TestCase):
    def test_language_selection_payload_contains_all_language_buttons(self):
        payload = json.loads(get_language_selection_payload("12345"))

        self.assertEqual(payload["type"], "interactive")
        self.assertEqual(payload["interactive"]["type"], "button")
        button_ids = [button["reply"]["id"] for button in payload["interactive"]["action"]["buttons"]]
        button_titles = [button["reply"]["title"] for button in payload["interactive"]["action"]["buttons"]]
        self.assertEqual(button_ids, ["lang_urdu", "lang_pashto", "lang_english"])
        self.assertEqual(button_titles, ["اردو", "پښتو", "English"])

    def test_localized_menu_payload_uses_urdu_copy(self):
        payload = json.loads(get_localized_menu_payload("12345", "ur"))
        first_row = payload["interactive"]["action"]["sections"][0]["rows"][0]

        self.assertEqual(first_row["id"], "opt_1_ur")
        self.assertEqual(first_row["title"], "واٹس ایپ گروپ")

    def test_demo_response_text_is_language_specific(self):
        self.assertIn("یہ ایک ڈیمو جواب ہے", get_demo_response_text("ur", "opt_1_ur"))
        self.assertIn("This is a demo response", get_demo_response_text("en", "opt_1_en"))

    def test_demo_response_text_handles_simple_option_id(self):
        self.assertIn("This is a demo response", get_demo_response_text("en", "1"))

    def test_sub_centers_selection_returns_city_menu(self):
        payload = json.loads(get_localized_menu_payload("12345", "ur"))
        self.assertEqual(payload["interactive"]["action"]["sections"][0]["rows"][5]["id"], "opt_6_ur")


if __name__ == "__main__":
    unittest.main()
