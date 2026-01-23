import gi

gi.require_version("Gtk", "4.0")


from gi.repository import Gtk


def create_menu_model():
    menu_builder = Gtk.Builder()
    menu_xml = """
        <interface>
            <menu id="app_menu">
                <section>
                    <item>
                        <attribute name="label">Preferences</attribute>
                        <attribute name="action">app.preferences</attribute>
                    </item>
                </section>
                <section>
                    <item>
                        <attribute name="label">About</attribute>
                        <attribute name="action">app.about</attribute>
                    </item>
                    <item>
                        <attribute name="label">Quit</attribute>
                        <attribute name="action">app.quit</attribute>
                    </item>
                </section>
            </menu>
        </interface>
        """

    menu_builder.add_from_string(menu_xml)
    return menu_builder.get_object("app_menu")


def create_header_bar():
    header_bar = Gtk.HeaderBar()
    menu_button = Gtk.MenuButton()
    menu_model = create_menu_model()
    menu_button.set_menu_model(menu_model)
    header_bar.pack_end(menu_button)
    return header_bar
