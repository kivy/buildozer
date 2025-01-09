from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.listview import ListView
from kivy.uix.popup import Popup
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton

class StudentManagerApp(App):
    def build(self):
        self.students = []
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title Label
        self.title_label = Label(text="Student List", font_size=24, size_hint=(1, 0.1))
        self.root.add_widget(self.title_label)

        # ListView for Students
        self.list_view = ListView(item_strings=[], size_hint=(1, 0.6))
        self.root.add_widget(self.list_view)

        # Input Fields
        self.first_name_input = TextInput(hint_text="First Name", size_hint=(1, 0.1), background_color=(1, 1, 0, 1), foreground_color=(0, 0, 0, 1))
        self.root.add_widget(self.first_name_input)

        self.last_name_input = TextInput(hint_text="Last Name", size_hint=(1, 0.1), background_color=(1, 1, 0, 1), foreground_color=(0, 0, 0, 1))
        self.root.add_widget(self.last_name_input)

        self.age_input = TextInput(hint_text="Age", size_hint=(1, 0.1), background_color=(1, 1, 0, 1), foreground_color=(0, 0, 0, 1))
        self.root.add_widget(self.age_input)

        self.grade_input = TextInput(hint_text="Grade", size_hint=(1, 0.1), background_color=(1, 1, 0, 1), foreground_color=(0, 0, 0, 1))
        self.root.add_widget(self.grade_input)

        # Buttons
        self.add_button = Button(text="Add Student", size_hint=(1, 0.1), background_color=(0, 1, 0, 1))
        self.add_button.bind(on_press=self.add_student)
        self.root.add_widget(self.add_button)

        self.update_button = Button(text="Update Student", size_hint=(1, 0.1), background_color=(0, 0, 1, 1))
        self.update_button.bind(on_press=self.update_student)
        self.root.add_widget(self.update_button)

        self.delete_button = Button(text="Delete Student", size_hint=(1, 0.1), background_color=(1, 0, 0, 1))
        self.delete_button.bind(on_press=self.delete_student)
        self.root.add_widget(self.delete_button)

        return self.root

    def add_student(self, instance):
        first_name = self.first_name_input.text
        last_name = self.last_name_input.text
        age = self.age_input.text
        grade = self.grade_input.text

        if first_name and last_name and age and grade:
            self.students.append(f"{first_name} {last_name}, Age: {age}, Grade: {grade}")
            self.list_view.adapter.data.extend([f"{first_name} {last_name}, Age: {age}, Grade: {grade}"])
            self.list_view._trigger_reset_populate()
            self.first_name_input.text = ''
            self.last_name_input.text = ''
            self.age_input.text = ''
            self.grade_input.text = ''
        else:
            self.show_popup("Input Error", "Please fill in all fields.")

    def update_student(self, instance):
        if self.list_view.adapter.selection:
            selected_index = self.list_view.adapter.selection[0].index
            first_name = self.first_name_input.text
            last_name = self.last_name_input.text
            age = self.age_input.text
            grade = self.grade_input.text

            if first_name and last_name and age and grade:
                self.students[selected_index] = f"{first_name} {last_name}, Age: {age}, Grade: {grade}"
                self.list_view.adapter.data[selected_index] = f"{first_name} {last_name}, Age: {age}, Grade: {grade}"
                self.list_view._trigger_reset_populate()
                self.first_name_input.text = ''
                self.last_name_input.text = ''
                self.age_input.text = ''
                self.grade_input.text = ''
            else:
                self.show_popup("Input Error", "Please fill in all fields.")
        else:
            self.show_popup("Selection Error", "Please select a student to update.")

    def delete_student(self, instance):
        if self.list_view.adapter.selection:
            selected_index = self.list_view.adapter.selection[0].index
            del self.students[selected_index]
            del self.list_view.adapter.data[selected_index]
            self.list_view._trigger_reset_populate()
        else:
            self.show_popup("Selection Error", "Please select a student to delete.")

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

if __name__ == "__main__":
    StudentManagerApp().run()
