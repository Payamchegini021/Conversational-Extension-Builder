import reflex as rx
import asyncio
import zipfile
import os
import logging
from typing import TypedDict
import json

try:
    import google.generativeai as genai
except ImportError as e:
    logging.exception(f"Failed to import google.generativeai: {e}")
    genai = None


class ChatMessage(TypedDict):
    role: str
    content: str


class Requirements(TypedDict):
    name: str
    description: str
    target_browser: list[str]
    inject_urls: list[str]
    has_background_script: bool
    has_popup: bool
    has_options_page: bool


INITIAL_CHAT_MESSAGE = [
    {
        "role": "assistant",
        "content": "Hello! I can help you create a browser extension. What would you like your extension to be called?",
    }
]


class ChatState(rx.State):
    chat_history: list[ChatMessage] = INITIAL_CHAT_MESSAGE
    current_message: str = ""
    is_processing: bool = False
    api_key: str = rx.LocalStorage("")
    available_models: list[str] = ["gemini-1.5-flash"]
    selected_model: str = "gemini-1.5-flash"
    requirements: Requirements = {
        "name": "",
        "description": "",
        "target_browser": [],
        "inject_urls": [],
        "has_background_script": False,
        "has_popup": False,
        "has_options_page": False,
    }
    generation_complete: bool = False
    zip_path: str = ""
    show_error_toast: bool = False
    error_message: str = ""

    @rx.var
    def show_api_key_modal(self) -> bool:
        return self.api_key == ""

    @rx.event
    def save_api_key(self, form_data: dict[str, str]):
        key = form_data.get("api_key", "").strip()
        if key:
            self.api_key = key
            yield ChatState.list_models
        else:
            yield rx.toast.error("API Key cannot be empty.")

    @rx.event(background=True)
    async def list_models(self):
        async with self:
            if not self.api_key:
                return
        try:
            if not genai:
                raise ImportError("google.generativeai not installed.")
            genai.configure(api_key=self.api_key)
            models = await asyncio.to_thread(genai.list_models)
            model_names = []
            for m in models:
                if "generateContent" in m.supported_generation_methods:
                    model_id = m.name.replace("models/", "")
                    model_names.append(model_id)
            async with self:
                self.available_models = sorted(model_names)
                if self.selected_model not in self.available_models:
                    if "gemini-1.5-flash" in self.available_models:
                        self.selected_model = "gemini-1.5-flash"
                    elif self.available_models:
                        self.selected_model = self.available_models[0]
                    else:
                        self.selected_model = ""
        except Exception as e:
            logging.exception(f"Could not list models: {e}")
            async with self:
                self.error_message = f"Could not fetch Gemini models. Using defaults."
                self.show_error_toast = True
                self.available_models = ["gemini-1.5-flash", "gemini-1.5-pro"]
                if self.selected_model not in self.available_models:
                    self.selected_model = "gemini-1.5-flash"

    def _get_system_prompt(self) -> str:
        return f"""\nYou are an expert in creating browser extensions. Your goal is to help a user define the requirements for a browser extension through a conversation.\nThe user will talk to you, and you need to ask questions to fill out the following requirements structure.\nWhen you have a value for a field, add it. Do not ask for it again.\nOnce all requirements are gathered, tell the user they can generate the extension.\n\nCurrent requirements:\n{json.dumps(self.requirements, indent=2)}\n\nYour response MUST be a valid JSON object with two keys:\n1. "response": A friendly, conversational reply to the user.\n2. "requirements": The updated requirements JSON object. If you don't have new information for a field, keep the existing value.\n\nThe requirements structure is:\n{{\n    "name": "string",\n    "description": "string",\n    "target_browser": ["Chrome" | "Firefox"],\n    "inject_urls": ["url_pattern"],\n    "has_background_script": boolean,\n    "has_popup": boolean,\n    "has_options_page": boolean\n}}\n\nKeep your conversational response concise.\nAsk one question at a time.\nStart by asking for the extension name.\n"""

    @rx.event(background=True)
    async def process_message(self, form_data: dict[str, str]):
        message = form_data.get("message", "").strip()
        if not message:
            async with self:
                self.error_message = "Message cannot be empty."
                self.show_error_toast = True
            return
        async with self:
            if not self.api_key:
                self.error_message = "Please set your Gemini API key first."
                self.show_error_toast = True
                return
            self.is_processing = True
            self.chat_history.append({"role": "user", "content": message})
        try:
            if not genai:
                raise ImportError(
                    "google.generativeai not installed. Run `pip install google-generativeai`"
                )
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.selected_model)
            prompt_history = []
            for msg in self.chat_history:
                role = "model" if msg["role"] == "assistant" else msg["role"]
                prompt_history.append(
                    {"role": role, "parts": [{"text": msg["content"]}]}
                )
            conversation = model.start_chat(history=prompt_history[:-1])
            system_prompt = self._get_system_prompt()
            user_message = prompt_history[-1]["parts"][0]["text"]
            response = await conversation.send_message_async(
                f"{system_prompt}\n\nUser input: {user_message}"
            )
            response_text = response.text.strip()
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("AI response did not contain a valid JSON object.")
            json_str = response_text[json_start:json_end]
            parsed_response = json.loads(json_str)
            ai_message = parsed_response.get(
                "response", "I'm not sure how to respond to that. Could you try again?"
            )
            updated_requirements = parsed_response.get(
                "requirements", self.requirements
            )
            async with self:
                self.chat_history.append({"role": "assistant", "content": ai_message})
                self.requirements = updated_requirements
                self.is_processing = False
        except Exception as e:
            logging.exception(f"Error processing AI message: {e}")
            async with self:
                error_str = f"Sorry, there was an error with the AI service: {e}"
                self.error_message = error_str
                self.chat_history.append({"role": "assistant", "content": error_str})
                self.show_error_toast = True
                self.is_processing = False
        async with self:
            self.current_message = ""

    @rx.event(background=True)
    async def generate_extension(self):
        async with self:
            if not self.requirements["name"] or not self.requirements["description"]:
                self.error_message = "Extension name and description are required."
                self.show_error_toast = True
                return
            self.is_processing = True
            self.generation_complete = False
            self.zip_path = ""
        await asyncio.sleep(2)
        try:
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            dir_name = "".join(filter(str.isalnum, self.requirements["name"])).lower()
            if not dir_name:
                dir_name = "my_extension"
            ext_dir = upload_dir / dir_name
            if ext_dir.exists():
                import shutil

                shutil.rmtree(ext_dir)
            ext_dir.mkdir(exist_ok=True)
            manifest = self._create_manifest()
            with open(ext_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            if manifest.get("content_scripts"):
                content_script = """// Content script for your extension

console.log('Content script loaded!');"""
                with open(ext_dir / "content.js", "w") as f:
                    f.write(content_script)
            if manifest.get("background"):
                background_script = """// Background script for your extension

console.log('Background script loaded!');"""
                with open(ext_dir / "background.js", "w") as f:
                    f.write(background_script)
            if manifest.get("action"):
                popup_html = "<html><head><title>Popup</title><link rel='stylesheet' href='popup.css'></head><body><h1>Extension Popup</h1><script src='popup.js'></script></body></html>"
                popup_js = "console.log('Popup script loaded!');"
                popup_css = "body { width: 200px; font-family: sans-serif; text-align: center; }"
                with open(ext_dir / "popup.html", "w") as f:
                    f.write(popup_html)
                with open(ext_dir / "popup.js", "w") as f:
                    f.write(popup_js)
                with open(ext_dir / "popup.css", "w") as f:
                    f.write(popup_css)
            if manifest.get("options_ui"):
                options_html = "<html><head><title>Options</title><link rel='stylesheet' href='options.css'></head><body><h1>Extension Options</h1><script src='options.js'></script></body></html>"
                options_js = "console.log('Options script loaded!');"
                options_css = "body { width: 400px; font-family: sans-serif; }"
                with open(ext_dir / "options.html", "w") as f:
                    f.write(options_html)
                with open(ext_dir / "options.js", "w") as f:
                    f.write(options_js)
                with open(ext_dir / "options.css", "w") as f:
                    f.write(options_css)
            zip_filename = f"{dir_name}.zip"
            zip_filepath = upload_dir / zip_filename
            with zipfile.ZipFile(zip_filepath, "w") as zipf:
                for root, _, files in os.walk(ext_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, ext_dir)
                        zipf.write(file_path, arcname)
            async with self:
                self.zip_path = zip_filename
                self.generation_complete = True
                self.is_processing = False
        except Exception as e:
            logging.exception(f"Generation failed: {e}")
            async with self:
                self.error_message = f"Generation failed: {e}"
                self.show_error_toast = True
                self.is_processing = False

    def _create_manifest(self) -> dict:
        manifest = {
            "manifest_version": 3,
            "name": self.requirements["name"],
            "version": "1.0",
            "description": self.requirements["description"],
        }
        if self.requirements.get("has_background_script"):
            manifest["background"] = {"service_worker": "background.js"}
        if self.requirements.get("inject_urls"):
            manifest["content_scripts"] = [
                {"matches": self.requirements["inject_urls"], "js": ["content.js"]}
            ]
        if self.requirements.get("has_popup"):
            manifest["action"] = {"default_popup": "popup.html"}
        if self.requirements.get("has_options_page"):
            manifest["options_ui"] = {"page": "options.html", "open_in_tab": True}
        if "Firefox" in self.requirements.get("target_browser", []):
            manifest["browser_specific_settings"] = {
                "gecko": {
                    "id": f"{self.requirements['name'].lower().replace(' ', '-')}@example.com"
                }
            }
        return manifest

    @rx.event
    def trigger_error_toast(self):
        yield rx.toast(self.error_message, duration=5000)
        self.show_error_toast = False