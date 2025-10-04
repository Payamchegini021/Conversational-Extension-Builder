import reflex as rx


def instruction_step(
    browser: str, step: str, description: rx.Component
) -> rx.Component:
    return rx.el.div(
        rx.el.p(f"Step {step}:", class_name="font-semibold text-gray-900"),
        description,
        class_name="mb-2 text-base",
    )


def instructions_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Installation Instructions",
            class_name="text-2xl font-bold text-gray-900 mb-4",
        ),
        rx.el.div(
            rx.el.h3(
                "Google Chrome", class_name="text-xl font-semibold text-gray-900 mb-2"
            ),
            instruction_step(
                "chrome",
                "1",
                rx.el.p(
                    "Open Chrome and navigate to ",
                    rx.el.code("chrome://extensions"),
                    ".",
                ),
            ),
            instruction_step(
                "chrome",
                "2",
                rx.el.p(
                    "Enable 'Developer mode' using the toggle in the top right corner."
                ),
            ),
            instruction_step(
                "chrome",
                "3",
                rx.el.p(
                    "Click 'Load unpacked' and select the downloaded extension folder."
                ),
            ),
            class_name="mb-6",
        ),
        rx.el.div(
            rx.el.h3(
                "Mozilla Firefox", class_name="text-xl font-semibold text-gray-900 mb-2"
            ),
            instruction_step(
                "firefox",
                "1",
                rx.el.p(
                    "Open Firefox and navigate to ", rx.el.code("about:debugging"), "."
                ),
            ),
            instruction_step(
                "firefox", "2", rx.el.p("Click 'This Firefox' on the left sidebar.")
            ),
            instruction_step(
                "firefox",
                "3",
                rx.el.p(
                    "Click 'Load Temporary Add-on...' and select the ",
                    rx.el.code("manifest.json"),
                    " file from the downloaded folder.",
                ),
            ),
        ),
        class_name="p-6 bg-white border-t border-gray-200 mt-6",
    )