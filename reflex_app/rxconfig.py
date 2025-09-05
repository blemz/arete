import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    api_url="http://localhost:8000",
    frontend_port=3000,
    backend_port=8000,
    tailwind={
        "plugins": ["@tailwindcss/forms", "@tailwindcss/typography"]
    },
    # Enable custom CSS and JavaScript
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%",
    )
)