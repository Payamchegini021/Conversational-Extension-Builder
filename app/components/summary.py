import reflex as rx
from app.states.chat_state import ChatState


def requirement_item(label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.p(f"{label}:", class_name="font-semibold text-gray-900 w-1/3"),
        rx.el.p(value, class_name="text-gray-700 w-2/3 break-words"),
        class_name="flex items-start text-base border-b border-gray-200 py-3",
    )


def summary_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Extension Summary", class_name="text-2xl font-bold text-gray-900 mb-4"
        ),
        rx.el.div(
            requirement_item("Name", ChatState.requirements["name"]),
            requirement_item("Description", ChatState.requirements["description"]),
            requirement_item(
                "Target Browsers", ChatState.requirements["target_browser"].join(", ")
            ),
            requirement_item(
                "Inject URLs", ChatState.requirements["inject_urls"].join(", ")
            ),
            requirement_item(
                "Background Script",
                ChatState.requirements["has_background_script"].to_string(),
            ),
            requirement_item(
                "Popup UI", ChatState.requirements["has_popup"].to_string()
            ),
            requirement_item(
                "Options Page", ChatState.requirements["has_options_page"].to_string()
            ),
            class_name="mb-6",
        ),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    ChatState.is_processing & ~ChatState.generation_complete,
                    rx.el.div(
                        rx.icon(tag="loader-circle", class_name="animate-spin mr-2"),
                        "Generating...",
                        class_name="flex items-center justify-center",
                    ),
                    "Generate Extension",
                ),
                on_click=ChatState.generate_extension,
                disabled=ChatState.is_processing
                | (ChatState.requirements["name"] == ""),
                class_name="w-full h-[44px] bg-orange-500 text-white rounded-lg hover:bg-orange-600 active:bg-orange-700 disabled:bg-gray-400 font-semibold text-base",
            ),
            rx.cond(
                ChatState.generation_complete,
                rx.el.a(
                    rx.el.button(
                        rx.icon(tag="download", class_name="mr-2"),
                        "Download Extension (.zip)",
                        class_name="w-full h-[44px] mt-4 bg-green-500 text-white rounded-lg hover:bg-green-600 active:bg-green-700 flex items-center justify-center font-semibold text-base",
                    ),
                    href=rx.get_upload_url(ChatState.zip_path),
                    download=True,
                ),
            ),
            class_name="w-full",
        ),
        rx.cond(
            ChatState.show_error_toast,
            rx.el.div(on_mount=ChatState.trigger_error_toast),
        ),
        class_name="p-6 bg-white",
    )