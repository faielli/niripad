import sys

file_path = '/home/fede/Projects/editor_selfmade/main_window.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# The problem is that lines 196-199 are inside handle_replace_all, 
# and new_file is missing.

# Let's find where handle_replace_all starts and ends.
# And where the orphaned code is.

# In the read output:
# handle_replace_all is line 173 to 195 (approx)
# orphaned code is 196 to 199
# open_file is 201

# Let's just rewrite the whole class method section.

new_methods = """
    def show_search_dialog(self):
        self.search_dialog.show()

    def show_command_palette(self):
        self.command_palette.show()

    def show_keybindings_dialog(self):
        dialog = KeybindingsDialog(self.config_manager, self)
        if dialog.exec():
            self._create_menu()

    def handle_find(self, text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not text:
            return False

        editor = current_tab.editor
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if not is_regex:
            if editor.find(text, flags):
                return True
            # Wrap around
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            editor.setTextCursor(cursor)
            return editor.find(text, flags)
        else:
            # Regex find implementation
            content = editor.toPlainText()
            cursor = editor.textCursor()
            start_pos = cursor.position()
            
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            match = re.search(text, content[start_pos:], flags=regex_flags)
            
            if match:
                match_start = start_pos + match.start()
                match_end = start_pos + match.end()
                cursor.setPosition(match_start)
                cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)
                editor.setTextCursor(cursor)
                return True
            else:
                # Wrap around
                match = re.search(text, content, flags=regex_flags)
                if match:
                    cursor.setPosition(match.start())
                    cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                    editor.setTextCursor(cursor)
                    return True
        return False

    def handle_replace(self, search_text, replace_text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        cursor = editor.textCursor()
        
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(replace_text)
        else:
            # Find next and replace
            if self.handle_find(search_text, case_sensitive, is_regex):
                cursor = editor.textCursor()
                cursor.insertText(replace_text)
                editor.setTextCursor(cursor)

    def handle_replace_all(self, search_text, replace_text, case_sensitive, is_regex):
        current_tab = self.tabs.currentWidget()
        if not current_tab or not search_text:
            return

        editor = current_tab.editor
        content = editor.toPlainText()
        
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        if is_regex:
            new_content = re.sub(search_text, replace_text, content, flags=regex_flags)
        else:
            # Plain text replace all
            if case_sensitive:
                new_content = content.replace(search_text, replace_text)
            else:
                # Case insensitive replace
                pattern = re.compile(re.escape(search_text), regex_flags)
                new_content = pattern.sub(replace_text, content)
        
        if new_content != content:
            editor.setPlainText(new_content)
            current_tab.on_text_changed() # Mark as modified

    def new_file(self):
        tab = EditorTab()
        index = self.tabs.addTab(tab, tab.get_title())
        self.tabs.setCurrentIndex(index)
        tab.modified_changed.connect(lambda: self.update_tab_title(index))

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        
        if file_path:
            tab = EditorTab(file_path)
            index = self.tabs.addTab(tab, tab.get_title())
            self.tabs.setCurrentIndex(index)
            tab.modified_changed.connect(lambda: self.update_tab_title(index))
"""

# I'll find the line where show_search_dialog starts and replace everything from there to open_file
# Or just replace the whole class content if I can.

with open(file_path, 'r') as f:
    all_lines = f.readlines()

# Find index of show_search_dialog
start_idx = -1
for i, line in enumerate(all_lines):
    if "def show_search_dialog(self):" in line:
        start_idx = i
        break

# Find index of open_file
end_idx = -1
for i, line in enumerate(all_lines):
    if "def open_file(self, file_path=None):" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    # Replace from start_idx up to end_idx
    # Note: end_idx is the start of open_file, so we replace up to end_idx
    all_lines[start_idx:end_idx] = [new_methods + "\n"]
    
    with open(file_path, 'w') as f:
        f.writelines(all_lines)
    print("Successfully updated main_window.py")
else:
    print(f"Failed to find indices. start_idx: {start_idx}, end_idx: {end_idx}")
