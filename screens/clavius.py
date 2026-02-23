from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFloatingActionButton, MDIconButton
from kivymd.uix.tab.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.card.card import MDSeparator
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivy.properties import StringProperty
from kivymd.uix.tab.tab import MDTabs


class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass


class ClaviusButton(MDFloatingActionButton):

    key = StringProperty()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):

            # Traverse up to the Clavius screen
            parent = self.parent
            while parent and not isinstance(parent, Clavius):
                parent = parent.parent

            if not parent:
                return super().on_touch_down(touch)

            clavius_screen = parent

            # Get the current active tab
            current_tab = the_tabs.get_current_tab()

            # Assuming the structure: Tab -> MDBoxLayout -> MDCard -> MDBoxLayout -> ClaviusField
            # Traverse the children to find the ClaviusField
            for child in current_tab.walk():
                if isinstance(child, ClaviusField):
                    if self.key == 'backspace':
                        child.text = child.text[:-1]
                    else:
                        child.text += self.key  # Append the key to the field


class ClaviusField(MDTextField):
    def on_touch_down(self, touch):
        return


class Clavius(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rel = {}

    def show_main_peak(self):
        main_peak = self.manager.app.main_peak / 1000
        self.ids.main_peak.text = f'Main Peak: {main_peak:.4f} kHz'

    def on_enter(self):

        if self.ids.the_fucking_container.children:
            print('All children are killed!!')
            self.ids.the_fucking_container.clear_widgets()

        self.show_main_peak()


        md_tabs = MDTabs(
            id='tabs',
            background_color=self.manager.app.SKY_MIST

        )

        self.md_tabs = md_tabs

        global the_tabs

        the_tabs = md_tabs

        for i, (field, value) in enumerate(self.fields):

            the_field = field

            tab = Tab(
                id='tabs',
                tab_label_text=field.label[:-2],
                title=field.label[:-2],
                icon=f'numeric-{i}-box-multiple', # I don't know!
            )

            if tab.title == self.active_tab:
                self.current_tab = tab

            layout = MDBoxLayout(
                padding=20,
            )

            title = MDLabel(
                size_hint=(1, .1),
                text=field.dialog_title,
                font_style='H4'
            )

            field_layout = MDBoxLayout(
                size_hint=(1, .9)
            )

            field = ClaviusField(
                text=value
            )

            self.rel[the_field] = field

            card = MDCard(
                orientation='vertical',
                padding=30
            )

            field_layout.add_widget(field)

            card.add_widget(title)
            card.add_widget(field_layout)

            layout.add_widget(card)

            tab.add_widget(layout)
            md_tabs.add_widget(tab)

        if getattr(self, "current_tab", None):
            md_tabs.switch_tab(self.current_tab.tab_label)

        self.ids.the_fucking_container.add_widget(md_tabs)


    def switch_tab(self, direction):
        tab_list = self.md_tabs.get_tab_list()
        current_tab = self.md_tabs.get_current_tab().tab_label

        if current_tab is None or not tab_list:
            return

        current_index = tab_list.index(current_tab)

        if direction == "next":
            new_index = (current_index + 1) % len(tab_list)
        elif direction == "prev":
            new_index = (current_index - 1) % len(tab_list)
        else:
            return  # Invalid direction

        self.md_tabs.switch_tab(tab_list[new_index])

    def save(self):

        for field, value in self.fields:
            field.ids.label_field.text = self.rel[field].text

        self.manager.current = 'modulus'
        self.manager.transition.direction = 'up'

