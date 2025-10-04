import reflex as rx
from app.states.chat_state import ChatState


def model_selector() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            "Select Model:",
            html_for="model_select",
            class_name="text-sm font-medium text-gray-700 mr-2",
        ),
        rx.el.select(
            rx.foreach(
                ChatState.available_models,
                lambda model: rx.el.option(model, value=model),
            ),
            id="model_select",
            value=ChatState.selected_model,
            on_change=ChatState.set_selected_model,
            disabled=ChatState.is_processing,
            class_name="w-full h-[44px] px-4 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-orange-500 text-base",
        ),
        class_name="flex items-center p-4 border-b border-gray-200",
    )


def chat_message(message: dict) -> rx.Component:
    is_user = message.get("role") == "user"
    return rx.el.div(
        rx.el.div(
            rx.el.p(message.get("content", ""), class_name="text-base"),
            class_name=rx.cond(
                is_user,
                "bg-orange-500 text-white rounded-t-2xl rounded-bl-2xl p-3",
                "bg-gray-200 text-gray-900 rounded-t-2xl rounded-br-2xl p-3",
            ),
            max_width="80%",
        ),
        class_name=rx.cond(is_user, "flex justify-end", "flex justify-start"),
        width="100%",
    )


def chat_interface(key: str) -> rx.Component:
    return rx.el.div(
        model_selector(),
        rx.el.div(
            rx.foreach(ChatState.chat_history, chat_message),
            class_name="flex flex-col gap-4 p-6 overflow-y-auto h-full",
            key=key,
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    placeholder="Type your message...",
                    name="message",
                    default_value=ChatState.current_message,
                    key=ChatState.current_message,
                    disabled=ChatState.is_processing,
                    class_name="w-full h-[44px] px-4 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-orange-500 text-base",
                ),
                rx.el.button(
                    rx.cond(
                        ChatState.is_processing,
                        rx.icon(tag="loader-circle", class_name="animate-spin"),
                        rx.icon(tag="send-horizontal"),
                    ),
                    type="submit",
                    disabled=ChatState.is_processing,
                    class_name="w-[44px] h-[44px] flex items-center justify-center bg-orange-500 text-white rounded-lg hover:bg-orange-600 active:bg-orange-700",
                ),
                class_name="flex items-center gap-2 p-4 border-t border-gray-200",
            ),
            on_submit=ChatState.process_message,
            reset_on_submit=True,
            width="100%",
        ),
        class_name="flex flex-col h-full bg-neutral-50 border-r border-gray-200",
    )