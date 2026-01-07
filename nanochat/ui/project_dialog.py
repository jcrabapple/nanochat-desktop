"""
Project dialog for creating and editing projects.

Provides a dialog for managing project organization.
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject


# Available project colors
PROJECT_COLORS = [
    ('#4a9eff', 'Blue'),
    ('#ff6b6b', 'Red'),
    ('#51cf66', 'Green'),
    ('#ffd43b', 'Yellow'),
    ('#cc5de8', 'Purple'),
    ('#ff922b', 'Orange'),
    ('#20c997', 'Teal'),
    ('#f06595', 'Pink'),
]


class ProjectDialog(Gtk.Dialog):
    """Dialog for creating or editing a project"""

    __gtype_name__ = "ProjectDialog"

    def __init__(self, parent=None, project=None):
        """
        Initialize project dialog.

        Args:
            parent: Parent window
            project: Existing project dict to edit (None for new project)
        """
        title = "Edit Project" if project else "New Project"
        super().__init__(
            title=title,
            transient_for=parent,
            modal=True,
            use_header_bar=True
        )

        self.project = project
        self.selected_color = project.get('color', '#4a9eff') if project else '#4a9eff'

        self.set_default_size(400, 300)
        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI"""
        # Get content area
        content = self.get_content_area()
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_spacing(16)

        # Name entry
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        name_label = Gtk.Label(label="Project Name")
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        name_box.append(name_label)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("Enter project name...")
        if self.project:
            self.name_entry.set_text(self.project.get('name', ''))
        self.name_entry.connect("changed", self._on_name_changed)
        name_box.append(self.name_entry)

        content.append(name_box)

        # Color selection
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        color_label = Gtk.Label(label="Color")
        color_label.set_halign(Gtk.Align.START)
        color_label.add_css_class("heading")
        color_box.append(color_label)

        # Color buttons in a flow box
        self.color_flow = Gtk.FlowBox()
        self.color_flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.color_flow.set_max_children_per_line(8)
        self.color_flow.set_min_children_per_line(4)
        self.color_flow.set_homogeneous(True)
        self.color_flow.set_column_spacing(8)
        self.color_flow.set_row_spacing(8)

        self.color_buttons = {}
        for color_hex, color_name in PROJECT_COLORS:
            btn = self._create_color_button(color_hex, color_name)
            flow_child = Gtk.FlowBoxChild()
            flow_child.set_child(btn)
            self.color_flow.append(flow_child)
            self.color_buttons[color_hex] = btn

        color_box.append(self.color_flow)
        content.append(color_box)

        # Description (optional)
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        desc_label = Gtk.Label(label="Description (optional)")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("heading")
        desc_box.append(desc_label)

        self.desc_entry = Gtk.Entry()
        self.desc_entry.set_placeholder_text("Enter description...")
        if self.project and self.project.get('description'):
            self.desc_entry.set_text(self.project.get('description'))
        desc_box.append(self.desc_entry)

        content.append(desc_box)

        # Add buttons to header bar
        header = self.get_header_bar()

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.CANCEL))
        header.pack_start(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.OK))
        self.save_btn = save_btn
        header.pack_end(save_btn)

        # Initially disable save if name is empty
        self._update_save_button()

    def _create_color_button(self, color_hex: str, color_name: str) -> Gtk.Button:
        """Create a color selection button"""
        btn = Gtk.Button()
        btn.set_size_request(40, 40)
        btn.set_tooltip_text(color_name)
        btn.add_css_class("color-button")

        # Apply color styling
        css_provider = Gtk.CssProvider()
        css = f"""
            .color-button-{color_hex[1:]} {{
                background-color: {color_hex};
                border-radius: 20px;
                min-width: 40px;
                min-height: 40px;
            }}
            .color-button-{color_hex[1:]}:hover {{
                background-color: {color_hex};
                opacity: 0.8;
            }}
            .color-button-selected {{
                border: 3px solid white;
                box-shadow: 0 0 0 2px {color_hex};
            }}
        """
        css_provider.load_from_data(css.encode())
        btn.get_style_context().add_provider(
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        btn.add_css_class(f"color-button-{color_hex[1:]}")

        # Mark as selected if this is the current color
        if color_hex == self.selected_color:
            btn.add_css_class("color-button-selected")

        btn.connect("clicked", self._on_color_clicked, color_hex)
        return btn

    def _on_color_clicked(self, button, color_hex):
        """Handle color button click"""
        # Remove selection from previous color
        for hex_code, btn in self.color_buttons.items():
            btn.remove_css_class("color-button-selected")

        # Select new color
        button.add_css_class("color-button-selected")
        self.selected_color = color_hex

    def _on_name_changed(self, entry):
        """Handle name entry change"""
        self._update_save_button()

    def _update_save_button(self):
        """Enable/disable save button based on validation"""
        name = self.name_entry.get_text().strip()
        self.save_btn.set_sensitive(len(name) > 0)

    def get_project_data(self) -> dict:
        """
        Get the project data from the dialog.

        Returns:
            Dict with name, color, and description
        """
        return {
            'name': self.name_entry.get_text().strip(),
            'color': self.selected_color,
            'description': self.desc_entry.get_text().strip() or None
        }


class MoveToProjectDialog(Gtk.Dialog):
    """Dialog for moving a conversation to a project"""

    __gtype_name__ = "MoveToProjectDialog"

    def __init__(self, parent=None, projects=None, current_project_id=None):
        """
        Initialize move to project dialog.

        Args:
            parent: Parent window
            projects: List of project dicts with id, name, color
            current_project_id: Current project ID (or None)
        """
        super().__init__(
            title="Move to Project",
            transient_for=parent,
            modal=True,
            use_header_bar=True
        )

        self.projects = projects or []
        self.current_project_id = current_project_id
        self.selected_project_id = current_project_id

        self.set_default_size(300, 400)
        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI"""
        content = self.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)

        # Scrolled window for project list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # List box
        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("boxed-list")
        self.list_box.connect("row-activated", self._on_row_activated)

        # Add "No Project" option
        no_project_row = self._create_project_row(None, "No Project", "#808080")
        self.list_box.append(no_project_row)

        # Add projects
        for project in self.projects:
            row = self._create_project_row(
                project['id'],
                project['name'],
                project.get('color', '#4a9eff')
            )
            self.list_box.append(row)

        scrolled.set_child(self.list_box)
        content.append(scrolled)

        # Add buttons to header bar
        header = self.get_header_bar()

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.CANCEL))
        header.pack_start(cancel_btn)

        move_btn = Gtk.Button(label="Move")
        move_btn.add_css_class("suggested-action")
        move_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.OK))
        header.pack_end(move_btn)

    def _create_project_row(self, project_id, name, color) -> Gtk.ListBoxRow:
        """Create a project row for the list"""
        row = Gtk.ListBoxRow()
        row.project_id = project_id

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Color indicator
        color_dot = Gtk.DrawingArea()
        color_dot.set_size_request(16, 16)
        color_dot.set_content_width(16)
        color_dot.set_content_height(16)

        # Style the color dot
        css_provider = Gtk.CssProvider()
        css = f"""
            .project-color-dot {{
                background-color: {color};
                border-radius: 8px;
                min-width: 16px;
                min-height: 16px;
            }}
        """
        css_provider.load_from_data(css.encode())
        color_dot.get_style_context().add_provider(
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        color_dot.add_css_class("project-color-dot")
        box.append(color_dot)

        # Project name
        label = Gtk.Label(label=name)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        box.append(label)

        # Checkmark if currently selected
        if project_id == self.current_project_id:
            check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            box.append(check)

        row.set_child(box)
        return row

    def _on_row_activated(self, list_box, row):
        """Handle row selection"""
        self.selected_project_id = row.project_id

    def get_selected_project_id(self):
        """Get the selected project ID (None for no project)"""
        selected = self.list_box.get_selected_row()
        if selected:
            return selected.project_id
        return self.selected_project_id
