from pyodide.ffi import create_proxy
from js import document


# The @create_proxy decorator allows this function to be used as
# an event handler from JS code
@create_proxy
def on_click(event):
    print("Text Clicked:", event.target.textContent)


# This gets called once the page finished loading
def main():
    container = document.body.appendChild(document.createElement("div"))
    container.textContent = "Example Text"
    container.addEventListener("click", on_click)
