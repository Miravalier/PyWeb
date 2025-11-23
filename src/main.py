from .dom import body, MouseEvent


async def on_click(event: MouseEvent):
    print("Event:", event)
    print("Target:", event.target)
    print("Position:", event.x, event.y)
    print("Button:", event.button)


# This gets called once the page has finished loading
def main():
    example_text = body.add_child("p", classes=["example"], text="Example Text")
    example_text.add_event_listener("click", on_click)
