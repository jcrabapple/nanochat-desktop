import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, Gdk, GLib


class Sidebar(Gtk.Box):
    """Sidebar with conversation list and project organization"""

    __gsignals__ = {
        'new-chat': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'conversation-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'conversation-deleted': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'conversation-renamed': (GObject.SIGNAL_RUN_FIRST, None, (object, str)),
        'conversation-move-to-project': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'project-created': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'project-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'project-deleted': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'settings-clicked': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.set_size_request(280, -1)
        self.set_hexpand(False)  # Prevent horizontal expansion
        self.add_css_class("sidebar")

        # New Chat button
        self.new_chat_button = Gtk.Button(label="New Chat")
        self.new_chat_button.add_css_class("suggested-action")
        self.new_chat_button.set_margin_start(12)
        self.new_chat_button.set_margin_end(12)
        self.new_chat_button.set_margin_top(12)
        self.new_chat_button.set_margin_bottom(12)
        self.new_chat_button.connect("clicked", self.on_new_chat)
        self.append(self.new_chat_button)

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search conversations...")
        self.search_entry.set_margin_start(12)
        self.search_entry.set_margin_end(12)
        self.search_entry.set_margin_bottom(12)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.append(self.search_entry)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(separator)

        # Scrolled window for projects and conversation list
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_vexpand(True)

        # Main content box inside scrolled window
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Projects section (collapsible)
        self.projects_section = self._create_projects_section()
        self.content_box.append(self.projects_section)

        # Separator between projects and conversations
        self.projects_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.projects_separator.set_margin_top(8)
        self.projects_separator.set_margin_bottom(8)
        self.content_box.append(self.projects_separator)

        # Conversation list box
        self.conversation_list = Gtk.ListBox()
        self.conversation_list.add_css_class("conversation-list")
        self.conversation_list.connect("row-activated", self.on_conversation_selected)
        self.content_box.append(self.conversation_list)

        self.scrolled.set_child(self.content_box)
        self.append(self.scrolled)

        # Separator before settings button
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_top(8)
        separator2.set_margin_bottom(8)
        self.append(separator2)

        # Settings button at bottom
        self.settings_button = Gtk.Button()
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        settings_box.set_halign(Gtk.Align.CENTER)
        settings_box.set_valign(Gtk.Align.CENTER)

        settings_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        settings_icon.set_pixel_size(18)
        settings_box.append(settings_icon)

        settings_label = Gtk.Label(label="Settings")
        settings_box.append(settings_label)

        self.settings_button.set_child(settings_box)
        self.settings_button.set_tooltip_text("Open Settings")
        self.settings_button.set_margin_start(12)
        self.settings_button.set_margin_end(12)
        self.settings_button.set_margin_bottom(12)
        self.settings_button.connect("clicked", self.on_settings_clicked)
        self.append(self.settings_button)

        # Store conversation and project data
        self.conversations = []
        self.all_conversations = []  # Store unfiltered conversations
        self.projects = []  # Store projects
        self.current_project_filter = None  # None = show all, int = filter by project

    def _create_projects_section(self) -> Gtk.Box:
        """Create the collapsible projects section"""
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header with expander
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_start(12)
        header_box.set_margin_end(12)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(8)

        # Projects label
        projects_label = Gtk.Label(label="PROJECTS")
        projects_label.add_css_class("conversation-group-header")
        projects_label.set_halign(Gtk.Align.START)
        projects_label.set_hexpand(True)
        header_box.append(projects_label)

        # Add project button
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.set_tooltip_text("Create new project")
        add_btn.add_css_class("flat")
        add_btn.connect("clicked", self._on_add_project_clicked)
        header_box.append(add_btn)

        section.append(header_box)

        # Projects list
        self.projects_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.projects_list.set_margin_start(12)
        self.projects_list.set_margin_end(12)
        section.append(self.projects_list)

        return section

    def _on_add_project_clicked(self, button):
        """Handle add project button click"""
        self.emit('project-created')

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        self.emit('settings-clicked')

    def on_new_chat(self, button):
        """Handle new chat button click"""
        self.emit('new-chat')

    def on_conversation_selected(self, list_box, row):
        """Handle conversation selection"""
        if row:
            conversation_id = row.conversation_id
            self.emit('conversation-selected', conversation_id)

    def populate_conversations(self, conversations: list):
        """
        Populate sidebar with conversations

        Args:
            conversations: List of conversation dicts with keys:
                          - id, title, updated_at, message_count
        """
        # Store all conversations for filtering
        self.all_conversations = conversations

        # Apply current search filter if any
        search_text = self.search_entry.get_text()
        if search_text:
            filtered = self._filter_conversations(conversations, search_text)
            self._display_conversations(filtered)
        else:
            self._display_conversations(conversations)

    def _display_conversations(self, conversations: list):
        """Internal method to display conversations"""
        # Clear existing
        while self.conversation_list.get_first_child() is not None:
            self.conversation_list.remove(self.conversation_list.get_first_child())

        self.conversations = conversations

        # Group conversations by date
        groups = self._group_by_date(conversations)

        # Add conversations in groups
        for group_name, convos in groups.items():
            # Group header
            header = Gtk.Label(label=group_name.upper())
            header.add_css_class("conversation-group-header")
            header.set_halign(Gtk.Align.START)
            header.set_margin_start(12)
            header.set_margin_top(12)
            header.set_margin_bottom(4)
            self.conversation_list.append(header)

            # Conversations in group
            for conv in convos:
                row = ConversationRow(conv)
                row.connect('delete-requested', self.on_delete_requested)
                row.connect('rename-requested', self.on_rename_requested)
                row.connect('move-to-project-requested', self.on_move_to_project_requested)
                self.conversation_list.append(row)

    def on_search_changed(self, search_entry):
        """Handle search text changes"""
        search_text = search_entry.get_text().strip().lower()

        if not search_text:
            # Show all conversations
            self._display_conversations(self.all_conversations)
        else:
            # Filter conversations
            filtered = self._filter_conversations(self.all_conversations, search_text)
            self._display_conversations(filtered)

    def _filter_conversations(self, conversations: list, search_text: str) -> list:
        """Filter conversations by search text"""
        return [
            conv for conv in conversations
            if search_text.lower() in conv['title'].lower()
        ]

    def _group_by_date(self, conversations: list) -> dict:
        """Group conversations by time periods"""
        from datetime import datetime, timedelta, timezone

        groups = {
            "Today": [],
            "Last 7 Days": [],
            "Last 30 Days": [],
            "Older": []
        }

        now = datetime.now(timezone.utc)
        today = now.date()
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)

        for conv in conversations:
            try:
                # Parse timestamp
                updated_at = datetime.fromisoformat(conv['updated_at'].replace('Z', '+00:00'))
                conv_date = updated_at.date()

                if conv_date == today:
                    groups["Today"].append(conv)
                elif conv_date >= seven_days_ago:
                    groups["Last 7 Days"].append(conv)
                elif conv_date >= thirty_days_ago:
                    groups["Last 30 Days"].append(conv)
                else:
                    groups["Older"].append(conv)
            except:
                # If parsing fails, put in "Older"
                groups["Older"].append(conv)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def on_delete_requested(self, row, conversation_id):
        """Handle delete request from conversation row"""
        self.emit('conversation-deleted', conversation_id)

    def on_rename_requested(self, row, conversation_id, new_title):
        """Handle rename request from conversation row"""
        self.emit('conversation-renamed', conversation_id, new_title)

    def on_move_to_project_requested(self, row, conversation_id):
        """Handle move to project request from conversation row"""
        self.emit('conversation-move-to-project', conversation_id)

    def set_active_conversation(self, conversation_id: int):
        """Highlight active conversation"""
        row = self.conversation_list.get_first_child()
        while row:
            if isinstance(row, ConversationRow) and row.conversation_id == conversation_id:
                self.conversation_list.select_row(row)
            row = row.get_next_sibling()

    # ==================== Project Management ====================

    def populate_projects(self, projects: list):
        """
        Populate projects section.

        Args:
            projects: List of project dicts with keys: id, name, color, conversation_count
        """
        self.projects = projects

        # Clear existing projects
        child = self.projects_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.projects_list.remove(child)
            child = next_child

        # Add "All Conversations" option - count will be updated when conversations are populated
        total_count = len(self.all_conversations) if self.all_conversations else 0
        all_btn = self._create_project_button(None, "All Conversations", "#808080", total_count)
        if self.current_project_filter is None:
            all_btn.add_css_class("project-selected")
        self.projects_list.append(all_btn)

        # Add each project
        for project in projects:
            btn = self._create_project_button(
                project['id'],
                project['name'],
                project.get('color', '#4a9eff'),
                project.get('conversation_count', 0)
            )
            if self.current_project_filter == project['id']:
                btn.add_css_class("project-selected")
            self.projects_list.append(btn)

        # Hide projects separator if no projects
        self.projects_separator.set_visible(len(projects) > 0)

    def _create_project_button(self, project_id, name: str, color: str, count: int) -> Gtk.Button:
        """Create a project button row"""
        btn = Gtk.Button()
        btn.add_css_class("flat")
        btn.add_css_class("project-row")
        btn.project_id = project_id

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Color indicator
        color_box = Gtk.Box()
        color_box.set_size_request(12, 12)

        # Apply color styling
        css_provider = Gtk.CssProvider()
        class_name = f"project-color-{project_id if project_id else 'all'}"
        css = f"""
            .{class_name} {{
                background-color: {color};
                border-radius: 6px;
                min-width: 12px;
                min-height: 12px;
            }}
        """
        css_provider.load_from_data(css.encode())
        color_box.get_style_context().add_provider(
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        color_box.add_css_class(class_name)
        box.append(color_box)

        # Project name
        label = Gtk.Label(label=name)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_ellipsize(True)
        box.append(label)

        # Conversation count
        count_label = Gtk.Label(label=str(count))
        count_label.add_css_class("dim-label")
        box.append(count_label)

        btn.set_child(box)
        btn.connect("clicked", self._on_project_clicked, project_id)

        # Add right-click menu for projects (not for "All")
        if project_id is not None:
            right_click = Gtk.GestureClick()
            right_click.set_button(3)
            right_click.connect("pressed", self._on_project_right_click, project_id)
            btn.add_controller(right_click)

        return btn

    def _on_project_clicked(self, button, project_id):
        """Handle project button click - filter conversations"""
        self.current_project_filter = project_id
        self.emit('project-selected', project_id)

        # Visual feedback - highlight selected project
        child = self.projects_list.get_first_child()
        while child:
            if hasattr(child, 'project_id'):
                if child.project_id == project_id:
                    child.add_css_class("project-selected")
                else:
                    child.remove_css_class("project-selected")
            child = child.get_next_sibling()

    def _on_project_right_click(self, gesture, n_press, x, y, project_id):
        """Show context menu for project"""
        if n_press == 1:
            widget = gesture.get_widget()

            popover = Gtk.Popover()
            popover.set_parent(widget)

            menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            menu_box.set_margin_start(8)
            menu_box.set_margin_end(8)
            menu_box.set_margin_top(8)
            menu_box.set_margin_bottom(8)

            # Delete button
            delete_btn = Gtk.Button(label="Delete Project")
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", lambda b: self._delete_project(project_id, popover))
            menu_box.append(delete_btn)

            popover.set_child(menu_box)
            popover.popup()

    def _delete_project(self, project_id, popover):
        """Delete a project"""
        popover.popdown()
        self.emit('project-deleted', project_id)

    def filter_by_project(self, project_id):
        """Filter conversations by project ID (None for all)"""
        self.current_project_filter = project_id

        if project_id is None:
            # Show all conversations
            self._display_conversations(self.all_conversations)
        else:
            # Filter by project
            filtered = [c for c in self.all_conversations if c.get('project_id') == project_id]
            self._display_conversations(filtered)


class ConversationRow(Gtk.ListBoxRow):
    """Single conversation row in sidebar"""

    __gsignals__ = {
        'delete-requested': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'rename-requested': (GObject.SIGNAL_RUN_FIRST, None, (object, str)),
        'move-to-project-requested': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, conversation: dict):
        super().__init__()

        self.conversation_id = conversation['id']
        self.original_title = conversation['title']
        self.is_editing = False

        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.main_box.set_margin_start(12)
        self.main_box.set_margin_end(12)
        self.main_box.set_margin_top(8)
        self.main_box.set_margin_bottom(8)

        # Title and metadata
        self.text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # Title
        self.title_label = Gtk.Label(label=conversation['title'])
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_ellipsize(True)  # Truncate with "..."
        self.title_label.set_width_chars(25)
        self.text_box.append(self.title_label)

        # Metadata (message count, time)
        metadata = f"{conversation.get('message_count', 0)} messages"
        meta_label = Gtk.Label(label=metadata)
        meta_label.add_css_class("dim-label")
        meta_label.set_halign(Gtk.Align.START)
        meta_label.set_size_request(200, -1)
        self.text_box.append(meta_label)

        self.main_box.append(self.text_box)

        # Delete button (trash icon, initially hidden)
        self.delete_button = Gtk.Button()
        trash_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        trash_icon.set_pixel_size(16)
        self.delete_button.set_child(trash_icon)
        self.delete_button.set_tooltip_text("Delete conversation")
        self.delete_button.add_css_class("delete-button")
        self.delete_button.set_opacity(0)  # Hidden initially
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.main_box.append(self.delete_button)

        self.set_child(self.main_box)

        # Add hover controller to the main box
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_hover_enter)
        hover_controller.connect("leave", self.on_hover_leave)
        self.main_box.add_controller(hover_controller)

        # Add double-click controller for rename
        click_controller = Gtk.GestureClick()
        click_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click_controller.connect("pressed", self.on_double_click)
        self.main_box.add_controller(click_controller)

        # Add right-click controller
        right_click_controller = Gtk.GestureClick()
        right_click_controller.set_button(3)  # Right click
        right_click_controller.connect("pressed", self.on_right_click)
        self.main_box.add_controller(right_click_controller)

    def on_double_click(self, gesture, n_press, x, y):
        """Handle double-click to start editing"""
        if n_press == 2:
            self.start_rename()

    def start_rename(self):
        """Start inline editing of the title"""
        if self.is_editing:
            return

        self.is_editing = True

        # Create entry for editing
        self.title_entry = Gtk.Entry()
        self.title_entry.set_text(self.original_title)
        self.title_entry.set_halign(Gtk.Align.START)
        self.title_entry.set_width_chars(25)

        # Replace label with entry
        parent = self.title_label.get_parent()
        parent.remove(self.title_label)
        parent.prepend(self.title_entry)

        # Connect signals
        self.title_entry.connect("activate", self.on_rename_activate)

        # Add focus controller for blur/focus-out (GTK4)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", self.on_rename_focus_leave)
        self.title_entry.add_controller(focus_controller)

        # Add key controller for Escape
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_rename_key_pressed)
        self.title_entry.add_controller(key_controller)

        # Focus and select all text
        self.title_entry.grab_focus()
        self.title_entry.set_position(-1)  # Move cursor to end
        # We need to select all after the widget is realized
        GLib.timeout_add(50, self._select_entry_text)

    def _select_entry_text(self):
        """Select all text in entry (called after widget is realized)"""
        if self.title_entry and self.is_editing:
            self.title_entry.grab_focus()
            # Select all text
            buffer = self.title_entry.get_buffer()
            self.title_entry.select_region(0, -1)
        return False  # Don't repeat

    def on_rename_activate(self, entry):
        """Handle Enter key in rename entry"""
        new_title = entry.get_text().strip()
        if new_title and new_title != self.original_title:
            self.original_title = new_title
            self.emit('rename-requested', self.conversation_id, new_title)
        self.finish_rename()

    def on_rename_focus_leave(self, controller):
        """Handle focus leave (GTK4 EventControllerFocus)"""
        if not self.is_editing or not self.title_entry:
            return
        # Save if changed, otherwise cancel
        new_title = self.title_entry.get_text().strip()
        if new_title and new_title != self.original_title:
            self.original_title = new_title
            self.emit('rename-requested', self.conversation_id, new_title)
        self.finish_rename()

    def on_rename_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press in rename entry"""
        if keyval == Gdk.KEY_Escape:
            # Cancel without saving
            self.finish_rename()
            return True
        return False

    def finish_rename(self):
        """Finish editing and restore label"""
        if not self.is_editing:
            return

        self.is_editing = False

        # Create new label with updated title
        new_label = Gtk.Label(label=self.original_title)
        new_label.set_halign(Gtk.Align.START)
        new_label.set_ellipsize(True)
        new_label.set_width_chars(25)

        # Replace entry with label
        parent = self.title_entry.get_parent()
        parent.remove(self.title_entry)
        parent.prepend(new_label)

        self.title_label = new_label
        self.title_entry = None

    def on_hover_enter(self, controller, x, y):
        """Show delete button on hover"""
        self.delete_button.set_opacity(1)

    def on_hover_leave(self, controller):
        """Hide delete button when hover ends"""
        self.delete_button.set_opacity(0)

    def on_delete_clicked(self, button):
        """Handle delete button click"""
        self.emit('delete-requested', self.conversation_id)

    def on_right_click(self, gesture, n_press, x, y):
        """Show context menu on right-click"""
        if n_press == 1:
            # Create popover menu
            popover = Gtk.Popover()
            popover.set_parent(self)

            # Position popover in the center of the row
            allocation = self.get_allocation()
            rect = Gdk.Rectangle()
            rect.x = allocation.width / 2
            rect.y = allocation.height / 2
            rect.width = 1
            rect.height = 1
            popover.set_pointing_to(rect)

            # Create menu box
            menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            menu_box.set_margin_start(8)
            menu_box.set_margin_end(8)
            menu_box.set_margin_top(8)
            menu_box.set_margin_bottom(8)

            # Move to Project button
            move_btn = Gtk.Button(label="Move to Project...")
            move_btn.add_css_class("flat")
            move_btn.connect("clicked", self._on_move_to_project, popover)
            menu_box.append(move_btn)

            # Separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.set_margin_top(4)
            separator.set_margin_bottom(4)
            menu_box.append(separator)

            # Delete button
            delete_btn = Gtk.Button(label="Delete")
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", self.on_context_delete_close, popover)
            menu_box.append(delete_btn)

            # Add to popover
            popover.set_child(menu_box)
            popover.popup()

    def _on_move_to_project(self, button, popover):
        """Handle move to project from context menu"""
        popover.popdown()
        self.emit('move-to-project-requested', self.conversation_id)

    def on_context_delete_close(self, widget, popover):
        """Handle delete from context menu and close popover"""
        popover.popdown()
        self.emit('delete-requested', self.conversation_id)

    def on_context_delete(self, widget):
        """Handle delete from context menu"""
        self.emit('delete-requested', self.conversation_id)

