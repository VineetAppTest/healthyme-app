from pathlib import Path

path = Path(__file__).resolve().parents[1] / "pages/15_Admin_Recipe_Manager.py"
text = path.read_text(encoding="utf-8")
start = text.index('        inactive_open = bool(st.session_state.get("hm_recipe_repository_inactive_open", False))')
end = text.index('\nwith add_tab:', start)
replacement = '''        inactive_open = bool(
            st.session_state.get("hm_recipe_repository_inactive_open", False)
        )
        if render_repository_disclosure(
            f"Inactive Repository Items ({len(inactive_df)})",
            is_open=inactive_open,
            key="recipe_repo_inactive_disclosure",
        ):
            st.session_state["hm_recipe_repository_inactive_open"] = not inactive_open
            st.rerun()
        if inactive_open:
            with repository_inactive_panel():
                if inactive_df.empty:
                    st.caption("No inactive repository items.")
                for index, row in inactive_df.iterrows():
                    label_col, action_col = st.columns([5.5, 1], gap="small")
                    with label_col:
                        st.markdown(
                            f"**{_clean(row.get('title')) or 'Untitled Recipe'}**  \\n{_recipe_summary(row)}"
                        )
                    with action_col:
                        if st.button(
                            "Reactivate",
                            key=f"recipe_repo_reactivate_{index}",
                            use_container_width=True,
                        ):
                            df.at[index, "status"] = "active"
                            save(df)
                            _flash("Recipe reactivated.")
                            st.rerun()
'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
