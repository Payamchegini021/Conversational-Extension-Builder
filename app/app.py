import reflex as rx
from app.components.chat import chat_interface
from app.components.summary import summary_panel
from app.components.instructions import instructions_panel
from app.components.api_key_modal import api_key_modal
from app.states.chat_state import ChatState


def index() -> rx.Component:
    return rx.el.main(
        api_key_modal(),
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "ExtensionGenius AI",
                    class_name="text-2xl font-bold text-gray-900 p-6 border-b border-gray-200",
                ),
                chat_interface(key=ChatState.chat_history.length().to_string()),
                class_name="flex flex-col h-screen",
            ),
            rx.el.div(
                summary_panel(),
                instructions_panel(),
                class_name="flex flex-col overflow-y-auto",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 h-screen w-screen font-['Montserrat'] bg-gray-100",
        ),
        class_name="font-['Montserrat'] bg-neutral-50",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)