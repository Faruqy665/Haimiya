"""
Haimiya - floating AI companion (main app)
-------------------------------------------
Ini layar utama (Kivy). Fungsinya:
- Nyimpen API key Groq
- Ngobrol sama Haimiya lewat Groq API
- Minta izin "muncul di atas aplikasi lain" (overlay)
- Nyalain/matiin service bubble (service/bubble.py)

PENTING: ganti nilai APP_PACKAGE di bawah supaya cocok dengan
package.domain + package.name di buildozer.spec kamu.
Contoh: kalau buildozer.spec isinya
    package.domain = org.haimiya
    package.name   = haimiya
maka APP_PACKAGE = "org.haimiya.haimiya"
"""

import os
import json
import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# --- Ganti sesuai buildozer.spec kamu (lihat catatan di atas) ---
APP_PACKAGE = "org.haimiya.haimiya"
SERVICE_JAVA_CLASS = APP_PACKAGE + ".ServiceBubble"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Cek model terbaru yang aktif di akun Groq-mu lewat console Groq
# atau endpoint GET /openai/v1/models kalau model ini nanti di-deprecate.
GROQ_MODEL = "llama-3.3-70b-versatile"

CONFIG_FILENAME = "haimiya_config.json"


def get_config_path():
    app = App.get_running_app()
    return os.path.join(app.user_data_dir, CONFIG_FILENAME)


def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data):
    with open(get_config_path(), "w") as f:
        json.dump(data, f)


class HaimiyaApp(App):
    def build(self):
        self.title = "Haimiya"
        self.history = []
        self.config_data = load_config()

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        # --- baris API key ---
        key_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        self.api_key_input = TextInput(
            text=self.config_data.get("groq_api_key", ""),
            hint_text="Groq API key",
            password=True,
            multiline=False,
        )
        save_key_btn = Button(text="Simpan", size_hint_x=None, width=dp(80))
        save_key_btn.bind(on_release=self.on_save_key)
        key_row.add_widget(self.api_key_input)
        key_row.add_widget(save_key_btn)
        root.add_widget(key_row)

        # --- baris kontrol overlay/service ---
        control_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        perm_btn = Button(text="Izin Overlay")
        perm_btn.bind(on_release=self.on_request_overlay_permission)
        start_btn = Button(text="Nyalakan Bubble")
        start_btn.bind(on_release=self.on_start_service)
        stop_btn = Button(text="Matikan")
        stop_btn.bind(on_release=self.on_stop_service)
        control_row.add_widget(perm_btn)
        control_row.add_widget(start_btn)
        control_row.add_widget(stop_btn)
        root.add_widget(control_row)

        # --- area chat ---
        self.chat_scroll = ScrollView()
        self.chat_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(4)
        )
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.chat_scroll.add_widget(self.chat_box)
        root.add_widget(self.chat_scroll)

        # --- baris input pesan ---
        input_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4))
        self.msg_input = TextInput(hint_text="Ngobrol sama Haimiya...", multiline=False)
        self.msg_input.bind(on_text_validate=self.on_send)
        send_btn = Button(text="Kirim", size_hint_x=None, width=dp(80))
        send_btn.bind(on_release=self.on_send)
        input_row.add_widget(self.msg_input)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        self.add_chat_line(
            "Haimiya",
            "Halo! Simpan API key Groq dulu di atas, terus kasih izin overlay "
            "kalau mau bubble-nya nongol di atas app lain.",
        )
        return root

    # ---------- konfigurasi ----------
    def on_save_key(self, *_):
        self.config_data["groq_api_key"] = self.api_key_input.text.strip()
        save_config(self.config_data)
        self.add_chat_line("Sistem", "API key disimpan.")

    # ---------- chat ----------
    def add_chat_line(self, sender, text):
        label = Label(
            text=f"[b]{sender}:[/b] {text}",
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - dp(32), None),
            halign="left",
            valign="top",
        )
        label.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))
        self.chat_box.add_widget(label)
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, "scroll_y", 0), 0.1)

    def on_send(self, *_):
        text = self.msg_input.text.strip()
        if not text:
            return
        api_key = self.config_data.get("groq_api_key", "")
        if not api_key:
            self.add_chat_line("Sistem", "Isi & simpan API key Groq dulu ya.")
            return

        self.msg_input.text = ""
        self.add_chat_line("Kamu", text)
        self.history.append({"role": "user", "content": text})
        threading.Thread(target=self._call_groq, args=(api_key,), daemon=True).start()

    def _call_groq(self, api_key):
        try:
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Kamu adalah Haimiya, AI companion yang ramah, "
                        "santai, dan jawabannya singkat.",
                    }
                ]
                + self.history[-20:],
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"(Gagal menghubungi Groq: {e})"

        self.history.append({"role": "assistant", "content": reply})
        Clock.schedule_once(lambda dt: self.add_chat_line("Haimiya", reply))

    # ---------- izin overlay & service ----------
    def on_request_overlay_permission(self, *_):
        try:
            from jnius import autoclass

            Settings = autoclass("android.provider.Settings")
            Uri = autoclass("android.net.Uri")
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            if not Settings.canDrawOverlays(activity):
                intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + activity.getPackageName()),
                )
                activity.startActivity(intent)
                self.add_chat_line(
                    "Sistem",
                    "Aktifkan izin 'Muncul di atas aplikasi lain' buat Haimiya, "
                    "lalu balik lagi ke sini.",
                )
            else:
                self.add_chat_line("Sistem", "Izin overlay sudah aktif.")
        except Exception as e:
            self.add_chat_line("Sistem", f"Cuma bisa dites di HP Android asli ({e}).")

    def on_start_service(self, *_):
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Settings = autoclass("android.provider.Settings")
            activity = PythonActivity.mActivity

            if not Settings.canDrawOverlays(activity):
                self.add_chat_line("Sistem", "Izinkan overlay dulu sebelum menyalakan bubble.")
                return

            ServiceClass = autoclass(SERVICE_JAVA_CLASS)
            ServiceClass.start(activity, "")
            self.add_chat_line("Sistem", "Bubble Haimiya dinyalakan.")
        except Exception as e:
            self.add_chat_line("Sistem", f"Gagal menyalakan service: {e}")

    def on_stop_service(self, *_):
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            ServiceClass = autoclass(SERVICE_JAVA_CLASS)
            activity = PythonActivity.mActivity
            activity.stopService(Intent(activity, ServiceClass))
            self.add_chat_line("Sistem", "Bubble Haimiya dimatikan.")
        except Exception as e:
            self.add_chat_line("Sistem", f"Gagal mematikan service: {e}")


if __name__ == "__main__":
    HaimiyaApp().run()
