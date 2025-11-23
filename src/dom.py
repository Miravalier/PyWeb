from __future__ import annotations

import inspect
import secrets
from enum import Enum
from js import document
from pyodide.ffi import create_proxy, JsNull
from typing import Callable, Optional


proxy_cache = {}


class Event:
    def __init__(self, proxy_event):
        self.proxy_event = proxy_event
        self.target = HtmlElement(proxy_event.target)

    @property
    def type(self) -> str:
        return self.proxy_event.type

    @property
    def timestamp(self) -> float:
        return self.proxy_event.timeStamp

    def prevent_default(self):
        self.proxy_event.preventDefault()

    def stop_propagation(self):
        self.proxy_event.stopPropagation()

    def __repr__(self):
        return f"[Event - {self.type}]"

    @staticmethod
    def lookup(proxy_event) -> Event:
        cls = event_map.get(proxy_event.type, Event)
        return cls(proxy_event)


class MouseButton(Enum):
    LEFT = 0
    WHEEL = 1
    RIGHT = 2
    BACK = 3
    FORWARD = 4


class MouseEvent(Event):
    def __repr__(self):
        return f"[MouseEvent - {self.type}]"

    @property
    def alt_pressed(self) -> bool:
        return self.proxy_event.altKey

    @property
    def ctrl_pressed(self) -> bool:
        return self.proxy_event.ctrlKey

    @property
    def meta_pressed(self) -> bool:
        return self.proxy_event.metaKey

    @property
    def shift_pressed(self) -> bool:
        return self.proxy_event.shiftKey

    @property
    def button(self) -> MouseButton:
        return MouseButton(self.proxy_event.button)

    @property
    def x(self) -> float:
        return self.proxy_event.offsetX

    @property
    def y(self) -> float:
        return self.proxy_event.offsetY

    @property
    def screen_x(self) -> float:
        return self.proxy_event.clientX

    @property
    def screen_y(self) -> float:
        return self.proxy_event.clientY


class WheelEvent(MouseEvent):
    def __repr__(self):
        return f"[WheelEvent - {self.type}]"

    @property
    def delta_x(self):
        return self.proxy_event.deltaX

    @property
    def delta_y(self):
        return self.proxy_event.deltaY


class KeyboardEvent(Event):
    def __repr__(self):
        return f"[KeyboardEvent - {self.type}]"

    @property
    def alt_pressed(self) -> bool:
        return self.proxy_event.altKey

    @property
    def ctrl_pressed(self) -> bool:
        return self.proxy_event.ctrlKey

    @property
    def meta_pressed(self) -> bool:
        return self.proxy_event.metaKey

    @property
    def shift_pressed(self) -> bool:
        return self.proxy_event.shiftKey

    @property
    def key(self) -> str:
        """
        Can be one of the following strings: "Backspace", "Tab", "Enter",
        "Escape", "Delete", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowUp",
        "End", "Home", "PageDown", "PageUp", or the unicode string of the key
        that was pressed.
        """
        return self.proxy_event.key


event_map = {
    "click": MouseEvent,
    "contextmenu": MouseEvent,
    "mousedown": MouseEvent,
    "mouseenter": MouseEvent,
    "mouseleave": MouseEvent,
    "mousemove": MouseEvent,
    "mouseout": MouseEvent,
    "mouseover": MouseEvent,
    "mouseup": MouseEvent,
    "wheel": WheelEvent,
    "keydown": KeyboardEvent,
    "keypress": KeyboardEvent,
    "keyup": KeyboardEvent,
}


class HtmlElement:
    def __init__(self, proxy_element):
        self.proxy_element = proxy_element

    def __repr__(self) -> str:
        id = self.id
        if id:
            return f"HtmlElement<{self.element_type} #{id}>"
        else:
            return f"HtmlElement<{self.element_type}>"

    @property
    def id(self) -> str:
        return self.proxy_element.id

    @property
    def width(self) -> int:
        return self.proxy_element.clientWidth

    @property
    def height(self) -> int:
        return self.proxy_element.clientHeight

    @property
    def element_type(self) -> str:
        return self.proxy_element.localName

    @property
    def text(self) -> str:
        return self.proxy_element.textContent

    @property
    def parent(self) -> HtmlElement:
        return HtmlElement(self.proxy_element.parentElement)

    @property
    def children(self) -> list[HtmlElement]:
        results = []
        for child in self.proxy_element.children:
            results.append(HtmlElement(child))
        return results

    @property
    def active_event_listeners(self) -> list[str]:
        try:
            return self.proxy_element.dataset.pyids.split(",")
        except AttributeError:
            return []

    @text.setter
    def text(self, value: str):
        self.proxy_element.textContent = value

    def delete(self):
        self.proxy_element.style.display = "none"
        for child in self.children:
            child.delete()
        self.remove_all_event_listeners()
        self.proxy_element.remove()

    def add_child(self,
                  element_type: str = "div",
                  *,
                  id: str = None,
                  classes: list[str] = None,
                  text: str = None,
                  ) -> HtmlElement:
        """
        Accepts a string with an HTML element type: "div", "input", etc
        """
        child_js_element = document.createElement(element_type)
        if classes is not None:
            for class_name in classes:
                child_js_element.classList.add(class_name)
        if id is not None:
            child_js_element.id = id
        if text is not None:
            child_js_element.textContent = text
        self.proxy_element.appendChild(child_js_element)
        return HtmlElement(child_js_element)

    def find_one(self, selector: str) -> Optional[HtmlElement]:
        result = self.proxy_element.querySelector(selector)
        if isinstance(result, JsNull):
            return None
        return HtmlElement(result)

    def find_many(self, selector: str) -> list[HtmlElement]:
        results = []
        for result in self.proxy_element.querySelectorAll(selector):
            results.append(HtmlElement(result))
        return results

    def add_class(self, class_name: str):
        self.proxy_element.classList.add(class_name)

    def remove_class(self, class_name: str):
        self.proxy_element.classList.remove(class_name)

    def toggle_class(self, class_name: str):
        self.proxy_element.classList.toggle(class_name)

    def has_class(self, class_name: str) -> bool:
        return self.proxy_element.classList.contains(class_name)

    def add_event_listener(self, event_name: str, callback: Callable) -> str:
        """
        Returns an identifier that can be passed to remove_event_listener()
        at a later time.
        """
        if inspect.iscoroutinefunction(callback):
            async def callback_wrapper(proxy_event):
                await callback(Event.lookup(proxy_event))
        else:
            def callback_wrapper(proxy_event):
                callback(Event.lookup(proxy_event))
        identifier = secrets.token_hex(8)
        proxy_callback = create_proxy(callback_wrapper)
        proxy_cache[identifier] = (event_name, proxy_callback)
        active_event_listeners = self.active_event_listeners
        active_event_listeners.append(identifier)
        self.proxy_element.dataset.pyids = ",".join(active_event_listeners)
        self.proxy_element.addEventListener(event_name, proxy_callback)
        return identifier

    def remove_event_listener(self, identifier: str):
        """
        Remove an event listener added previously from python. Cannot be used
        to remove event listeners added in JS.
        """
        event_name, proxy_callback = proxy_cache.pop(identifier, None)
        self.proxy_element.removeEventListener(event_name, proxy_callback)
        proxy_callback.destroy()
        active_event_listeners = self.active_event_listeners
        active_event_listeners.remove(identifier)
        self.proxy_element.dataset.pyids = ",".join(active_event_listeners)

    def remove_all_event_listeners(self):
        """
        Remove all event listeners previous added from python. Cannot be used
        to remove event listeners added in JS.
        """
        for identifier in self.active_event_listeners:
            event_name, proxy_callback = proxy_cache.pop(identifier, (None, None))
            if proxy_callback is None:
                continue
            self.proxy_element.removeEventListener(event_name, proxy_callback)
            proxy_callback.destroy()
        self.proxy_element.dataset.pyids = ""


body = HtmlElement(document.body)
