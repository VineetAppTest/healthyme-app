from __future__ import annotations


def install_member_exercise_journal_table() -> None:
    """Replace only the shared Exercise Journal renderer.

    Daily Log and the standalone Member Exercise page already import the shared
    renderer from ``components.member_exercise_journal``. Rebinding that one callable
    keeps both entry points aligned without changing their routing or page contracts.
    """

    from components import member_exercise_journal as journal
    from components.member_exercise_journal_table import (
        render_member_exercise_journal_table,
    )

    if getattr(journal, "_hm_editable_table_installed", False):
        return
    journal._hm_editable_table_installed = True
    journal.render_member_exercise_journal = render_member_exercise_journal_table
