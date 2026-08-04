from pathlib import Path


path = Path("tests/test_member_home_schedule_presentation.py")
text = path.read_text()
old = '''        self.assertLess(
            source.index("_render_upcoming_schedules(user_id)"),
            source.index("_render_messages(user_id, show_divider="),
        )'''
new = '''        self.assertLess(
            source.rindex("_has_upcoming_schedule = _render_upcoming_schedules(user_id)"),
            source.rindex("_render_messages(user_id, show_divider=_has_upcoming_schedule)"),
        )'''
if text.count(old) != 1:
    raise RuntimeError(f"Expected one execution-order assertion, found {text.count(old)}")
path.write_text(text.replace(old, new, 1))
