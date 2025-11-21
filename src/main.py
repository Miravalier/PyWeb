from js import document


def main():
    container = document.body.appendChild(document.createElement("div"))
    container.textContent = "Example Text"
