import flet

form_submitted = flet.Text("", size=24, weight=flet.FontWeight.W_600, color='green')

def form_submit_function(e):
    form_submitted.value = 'form submitted!'

form_container = flet.Container(
    flet.Column([
        flet.Text("Sign Up", size=24, color='black', weight='w600'),
        flet.TextField(
            label="First Name", text_size=16, border_radius=14, color='black',
            focused_border_color="#0a5ff", border_width=0.6, border_color='black'
        ),
        flet.TextField(
            label="Email", text_size=16, border_radius=14, color='black',
            focused_border_color="#0a5ff", border_width=0.6, border_color='black'
        ),
        flet.TextField(
            label="Password", password=True, can_reveal_password=True, text_size=16, border_radius=14,
            focused_border_color="#0a5ff", border_width=0.6, border_color='black', color='black',
        ),
        flet.Button(
            "Submit", color='white',
            width=700, height=40, style=flet.ButtonStyle(
                text_style=flet.TextStyle(size=16, weight='w600'),
                bgcolor='#0a85ff'
            ),
            on_click=form_submit_function
        ),
        form_submitted
    ], horizontal_alignment='center', spacing=20),
    width=400, height=400, bgcolor='white',
    border_radius=18, padding=20
)

def main(page:flet.Page):
    page.window.width = 600
    page.window.height = 500
    page.bgcolor = "#e6e6e6"
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.add(
        form_container
    )

flet.app(main)