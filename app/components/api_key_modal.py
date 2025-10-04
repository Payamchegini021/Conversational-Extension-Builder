import reflex as rx
from app.states.chat_state import ChatState


def api_key_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                "Enter your Gemini API Key", class_name="text-lg font-semibold"
            ),
            rx.dialog.description(
                "You need to provide your own Gemini API key to use the chat features. Your key will be stored locally in your browser.",
                class_name="text-sm text-gray-600 mt-1",
            ),
            rx.el.form(
                rx.el.input(
                    placeholder="Enter your API Key",
                    name="api_key",
                    type="password",
                    class_name="w-full mt-4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500",
                ),
                rx.el.button(
                    "Save",
                    type="submit",
                    class_name="mt-4 w-full bg-orange-500 text-white py-2 rounded-md hover:bg-orange-600 font-semibold",
                ),
                on_submit=ChatState.save_api_key,
                width="100%",
            ),
            class_name="bg-white p-6 rounded-lg shadow-lg",
            style={"max_width": "450px"},
        ),
        open=ChatState.show_api_key_modal,
    )