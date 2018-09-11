import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.button import Button

class DummyApp(App):
    def build(self):
        return Button(text="Hello World")

if __name__ == '__main__':
    DummyApp().run()
