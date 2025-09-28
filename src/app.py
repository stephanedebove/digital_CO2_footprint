from typing import Optional

import streamlit as st
from loguru import logger

from calculator import calculate_co2e_offsetting, compute_total_kg_co2e
from loader import Assumptions, load_assumptions
from translations import (
    _LANG,
    _TEXTS,
    T,
    format_float,
    localize_decimals_in_text,
    set_language,
)


def number_input_localized(
    label: str,
    value: float,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    step: Optional[float] = None,
    key: Optional[str] = None,
    label_visibility: str = "visible",
    decimals: int = 2,
) -> float:
    """Locale-aware numeric input for Streamlit.

    Uses a comma as decimal separator for French by rendering a text input and
    converting commas to dots internally. For non-French languages, falls back
    to Streamlit's number_input with a printf-style format string.

    Args:
        label: Widget label.
        value: Default numeric value.
        min_value: Minimum allowed value (inclusive) or None.
        max_value: Maximum allowed value (inclusive) or None.
        step: Step size for increments (only used in non-French mode).
        key: Optional Streamlit key.
        label_visibility: Streamlit label visibility.

    Returns:
        The parsed float value, clamped to [min_value, max_value] when provided.
    """
    if _LANG == "fr":
        display_value = format_float(value, decimals)
        raw = st.text_input(
            label=label,
            value=display_value,
            key=key,
            label_visibility=label_visibility,
        )
        # Normalize French input: allow spaces as thousands separators, comma as decimal.
        normalized = (raw or "").replace("\xa0", "").replace(" ", "").replace(",", ".")
        try:
            parsed = float(normalized)
        except Exception:
            parsed = value
        if min_value is not None:
            parsed = max(min_value, parsed)
        if max_value is not None:
            parsed = min(max_value, parsed)
        # Round to configured decimals to match YAML precision contract
        return round(parsed, decimals)
    return st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        key=key,
        label_visibility=label_visibility,
        format=f"%0.{decimals}f",
    )
    # The return happens via Streamlit; round the result to ensure stored precision matches YAML
    # Note: We can't capture the result here without rendering twice, so rounding is handled by callers.


def render_source(variable: str) -> None:
    """Render a variable-level source (single string) under the related sidebar input, with in-place clickable URLs.

    Args:
        variable: Variable name whose source should be displayed (e.g. 'video_bitrate_mbps').

    """
    # Check if the variable exists in the _TEXTS dictionary for the current language
    src_val = _TEXTS.get(_LANG, {}).get(f"{variable}_source", None)
    if not src_val:
        return

    import re

    def linkify_urls(text: str) -> str:
        url_re = re.compile(r"(https?://[^\s,;]+)")
        return url_re.sub(r"[\1](\1)", text)

    # Display "Source:" and the source text on the same line, smaller font
    st.markdown(
        f"<span style='font-size:0.85em; color:gray;'>Source(s) pour les valeurs par défaut : </span>"
        f"<span style='font-size:0.85em'>{linkify_urls(src_val)}</span>",
        unsafe_allow_html=True,
    )


def _neutralize_markdown_codeblocks(text: str) -> str:
    """Prevent accidental Markdown code-blocks caused by leading spaces.

    Markdown treats lines starting with four or more spaces as a code block. This
    function replaces leading groups of four spaces with non-breaking spaces so
    that visual indentation is preserved without triggering code formatting.

    Args:
        text: The original Markdown text possibly containing indented lines.

    Returns:
        The text with leading indentation neutralized to avoid code blocks.
    """
    import re

    def repl(match: re.Match[str]) -> str:
        # Replace each group of exactly four spaces by two NBSP characters.
        # This keeps indentation feel without being considered indentation by Markdown.
        leading = match.group(1)
        return leading.replace("    ", "\u00a0\u00a0")

    # Only transform indentation at the start of lines.
    return re.sub(r"(?m)^( {4,})", repl, text)


def _render_plain_text_preserve_whitespace(text: str) -> None:
    """Render plain text preserving line breaks and indentation without code block styling.

    Uses an HTML wrapper with CSS white-space: pre-wrap so that newlines and sequences
    of spaces are preserved. The text is HTML-escaped to ensure it's displayed as text.

    Args:
        text: The raw text to render.
    """
    import html

    safe = html.escape(text)
    st.markdown(
        f"<div style='white-space: pre-wrap; font-family: inherit;'>{safe}</div>",
        unsafe_allow_html=True,
    )


def _prepare_markdown_preserve_layout(text: str) -> str:
    """Prepare Markdown text to preserve indentation and line breaks without code blocks.

    - Converts leading spaces on each line to non-breaking spaces so Markdown doesn't
        treat them as code blocks and the visual indentation is kept.
    - Converts newlines to Markdown hard line breaks (two spaces + newline) so that
        line breaks are respected without requiring HTML.

    Args:
            text: The Markdown content to normalize.

    Returns:
            A Markdown string that keeps layout and still renders bold/italics, etc.
    """
    import re

    # Replace any leading spaces with NBSP on each line to avoid code block detection
    def lead_spaces_to_nbsp(match: re.Match[str]) -> str:
        spaces = match.group(1)
        return "\u00a0" * len(spaces)

    text = re.sub(r"(?m)^( +)", lead_spaces_to_nbsp, text)

    # Force line breaks for each newline by adding two spaces before the newline
    # This keeps paragraphs if there are blank lines as well.
    lines = text.split("\n")
    text = "  \n".join(lines)
    return text


def render_compute_button(label: str) -> bool:
    """Render a large, centered compute button with a green background.

    The button is centered using a 1-2-1 column layout and stretched to the
    column width. Styles are applied via CSS to increase size and set color.

    Args:
        label: The text to display on the button.

    Returns:
        True if the button was clicked, False otherwise.
    """
    # Inject scoped CSS (versioned) to avoid duplication and override previous styles
    if st.session_state.get("_compute_btn_css_version") != 2:
        st.markdown(
            """
            <style>
            /* Scoped styles to only the compute button container */
            #compute-btn div.stButton > button,
            #compute-btn div.stButton > button:hover,
            #compute-btn div.stButton > button:active,
            #compute-btn div.stButton > button:focus,
            #compute-btn div.stButton > button:focus-visible {
                /* Keep default theme colors, just make it bigger */
                background-color: var(--background-color) !important;
                color: var(--text-color) !important;
                border: 1px solid var(--secondary-background-color) !important;
                padding: 14px 28px !important;
                font-size: 20px !important;
                border-radius: 6px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["_compute_btn_css_version"] = 2

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Use container width to make the button occupy the center column
        st.markdown("<div id='compute-btn'>", unsafe_allow_html=True)
        clicked = st.button(label, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return clicked


def render_assumptions_section(
    assumptions: Assumptions, assumptions_dict: dict, default_streamlit_widget
) -> None:
    """Render a section of assumptions dynamically based on a dictionary."""

    def safe_float(value):
        return float(value) if value is not None else None

    min_value = 0.0
    max_value = 100.0 if default_streamlit_widget == st.slider else None

    for variable, metadata in assumptions_dict.items():
        st.subheader(T(variable))
        render_source(variable)
        if isinstance(getattr(assumptions, variable), dict):
            # if the variable has subitems (is a dict), render each subitem with its own widget
            total = 0.0
            for subitem, value in getattr(assumptions, variable).items():
                # code to display the streamlit widget for each subitem:
                # getattr() part is the widget instance, e.g. st.slider(...),
                # followed by widget parameters in ()
                widget = metadata.get("streamlit_widget", default_streamlit_widget)
                if widget == st.number_input:
                    decs = assumptions.get_decimals(variable, subitem)
                    getattr(assumptions, variable)[subitem] = number_input_localized(
                        label=T(f"{variable}_{subitem}"),
                        min_value=safe_float(metadata.get("min_value", min_value)),
                        max_value=safe_float(metadata.get("max_value", max_value)),
                        value=float(value),
                        key=f"{variable}_{subitem}_input",
                        decimals=decs,
                    )
                else:
                    # Slider: step and display format based on YAML decimals
                    decs = assumptions.get_decimals(variable, subitem)
                    step_val = 10 ** (-decs) if decs > 0 else 1.0
                    getattr(assumptions, variable)[subitem] = widget(
                        label=T(f"{variable}_{subitem}"),
                        min_value=safe_float(metadata.get("min_value", min_value)),
                        max_value=safe_float(metadata.get("max_value", max_value)),
                        value=float(value),
                        step=step_val,
                        format=(f"%0.{decs}f" if decs > 0 else "%d"),
                        key=f"{variable}_{subitem}_slider",
                    )
                total += getattr(assumptions, variable)[subitem]
            if metadata.get("sum_should_be", None) is not None:
                # check if sum of subitems equals sum_should_be, if not, adjust the "variable_to_alter" subitem to make it so
                if not "variable_to_alter" in metadata:
                    raise ValueError(
                        f"Assumptions variable '{variable}' has 'sum_should_be' but no 'variable_to_alter' specified."
                    )
                if total < metadata["sum_should_be"]:
                    getattr(assumptions, variable)[metadata["variable_to_alter"]] += (
                        metadata["sum_should_be"] - total
                    )
                    st.info(T(f"{variable}_check"))
                elif total > metadata["sum_should_be"]:
                    st.error(T(f"{variable}_error").format(percent=total))
        else:
            # if the variable is a single value, render it with a single widget
            widget = metadata.get("streamlit_widget", default_streamlit_widget)
            if widget == st.number_input:
                decs = assumptions.get_decimals(variable)
                setattr(
                    assumptions,
                    variable,
                    number_input_localized(
                        label=T(variable),
                        min_value=safe_float(metadata.get("min_value", min_value)),
                        max_value=safe_float(metadata.get("max_value", max_value)),
                        value=float(getattr(assumptions, variable)),
                        label_visibility="collapsed",
                        key=f"{variable}_input",
                        decimals=decs,
                    ),
                )
            else:
                # Slider: step and display format based on YAML decimals
                decs = assumptions.get_decimals(variable)
                step_val = 10 ** (-decs) if decs > 0 else 1.0
                setattr(
                    assumptions,
                    variable,
                    widget(
                        label=T(variable),
                        min_value=safe_float(metadata.get("min_value", min_value)),
                        max_value=safe_float(metadata.get("max_value", max_value)),
                        value=float(getattr(assumptions, variable)),
                        step=step_val,
                        format=(f"%0.{decs}f" if decs > 0 else "%d"),
                        label_visibility="collapsed",
                        key=f"{variable}_slider",
                    ),
                )


def render_sidebar(assumptions: Assumptions) -> Assumptions:
    # dictionary of variables to render in the sidebar as main assumptions. Default streamlit widget will be st.slider, min value 0, max value 100, except if you override it here:
    main_assumptions = {
        "device_percent": {
            "sum_should_be": 100.0,
            "variable_to_alter": "computer",
        },
        "fixed_network_percent": {},
        # New per-network resolution percents (each group sums to 100)
        "fixed_network_resolution_percent": {
            "sum_should_be": 100.0,
            "variable_to_alter": "1080p",
        },
        "mobile_network_resolution_percent": {
            "sum_should_be": 100.0,
            "variable_to_alter": "1080p",
        },
    }
    # dictionary of variables to render in the sidebar as main assumptions. Default streamlit widget will be st.number_input, min value 0, max_value None, except if you override it here:

    secondary_assumptions = {
        "device_production_kg_co2e": {},
        "device_lifetime_hours": {},
        "device_watts": {},
        "co2e_per_kWh": {},
        "network_kwh_per_gb": {},
        "network_kwh_per_user_per_hour": {},
        "datacenter_kg_co2e": {},
        "video_bitrate_GB_per_hour": {},
        "co2e_offsetting": {},
    }

    st.sidebar.header(T("main_assumptions_header"))
    with st.sidebar.expander(T("main_assumptions_edit"), expanded=False):
        render_assumptions_section(assumptions, main_assumptions, st.slider)

    st.sidebar.header(T("secondary_assumptions_header"))
    with st.sidebar.expander(T("secondary_assumptions_edit"), expanded=False):
        render_assumptions_section(assumptions, secondary_assumptions, st.number_input)

    st.session_state["assumptions"] = assumptions
    return assumptions


def render_language_switch() -> None:
    """Render language switch in sidebar and set current language."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    lang = st.sidebar.selectbox(
        T("language_label"),
        options=list(
            _TEXTS.keys()
        ),  # Dynamically fetch available languages from _TEXTS
        index=list(_TEXTS.keys()).index(st.session_state["lang"]),
        key="language_selectbox",
    )
    st.session_state["lang"] = lang
    set_language(st.session_state["lang"])


def flatten_assumptions(assumptions: dict) -> dict:
    """Flatten a nested dictionary by combining top-level and second-level keys.

    Args:
        assumptions: The original dictionary to flatten.

    Returns:
        A flattened dictionary with combined keys.
    """
    flattened = {}
    for key, value in assumptions.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                flattened[f"{key}_{subkey}"] = subvalue
        else:
            flattened[key] = value
    return flattened


def render_page(role: str, assumptions: Assumptions) -> None:
    """Render the page based on the role (producer or consumer) and compute CO2 footprint."""
    if role == "producer":
        st.write(T("producer_help"))
        hours_label = T("producer_watch_hours")
        result_label = T("result_total_kg")
    else:
        st.write(T("consumer_help"))
        hours_label = T("consumer_weekly_hours")
        result_label = T("result_total_kg_year")

    # Weekly hours input (integers only)
    def _hours_key() -> str:
        return "hours_input_key"

    # Initialize with YAML default to keep a single source of truth
    assumptions.hours_input = st.number_input(
        hours_label,
        min_value=0,
        value=int(getattr(assumptions, "hours_input", 30)),
        step=1,
        format="%d",
        key=_hours_key(),
    )

    if render_compute_button(T("compute_button")):
        kg_emitted, kg_emitted_with_production, intermediate_steps = (
            compute_total_kg_co2e(assumptions, role=role)
        )
        kg_emitted_display = format_float(kg_emitted, 2)
        kg_emitted_with_production_display = format_float(kg_emitted_with_production, 2)
        unit_suffix = f" {T('unit_per_year')}"

        st.write(T("result_with_production_prefix"))
        st.markdown(
            f"""
            <div style=\"display: flex; justify-content: center; margin-top: 8px;\">
                <button style=\"background-color: #4CAF50; color: white; border: none; padding: 10px 20px; 
                               text-align: center; text-decoration: none; display: inline-block; 
                               font-size: 30px; border-radius: 5px; cursor: default; margin-bottom: 10px;\">
                     {kg_emitted_with_production_display} {unit_suffix}
                </button>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(T("result_without_production_prefix"))
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 20px;">
                <button style=\"background-color: #4CAF50; color: white; border: none; padding: 10px 20px; 
                               text-align: center; text-decoration: none; display: inline-block; 
                               font-size: 30px; border-radius: 5px; cursor: default; margin-bottom: 20px;">
                     {kg_emitted_display} {unit_suffix}
                </button>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Explanation paragraph
        st.write(localize_decimals_in_text(T("result_explanation")))

        st.subheader(T("co2e_offsetting_title"))
        # Compute offsetting for both usage-only and with-production totals
        offsetting_usage = calculate_co2e_offsetting(
            kg_emitted, assumptions["co2e_offsetting"]
        )
        offsetting_with_prod = calculate_co2e_offsetting(
            kg_emitted_with_production, assumptions["co2e_offsetting"]
        )
        # Build a Markdown table with two columns (no index, no "Action" header),
        # each cell containing the sentence with the number embedded
        usage_col = T("offsetting_table_usage_only")
        with_prod_col = T("offsetting_table_with_production")
        header = f"| {usage_col} | {with_prod_col} |\n| --- | --- |\n"
        rows_md = []
        for action in assumptions["co2e_offsetting"].keys():
            usage_sentence = T(f"{action}_display").replace(
                "{x}", format_float(offsetting_usage.get(action, 0.0), 2)
            )
            with_prod_sentence = T(f"{action}_display").replace(
                "{x}", format_float(offsetting_with_prod.get(action, 0.0), 2)
            )
            rows_md.append(f"| {usage_sentence} | {with_prod_sentence} |")
        st.markdown(localize_decimals_in_text(header + "\n".join(rows_md)))

        assumptions_flattened = flatten_assumptions(assumptions.__dict__)
        st.subheader(T("details_subheader"))
        with st.expander(T("details_expander")):
            # Merge contexts to avoid duplicate keyword arguments in str.format
            fmt_ctx = {**intermediate_steps, **assumptions_flattened}
            formatted_details_text = T("details_text").format(**fmt_ctx)
            # Preserve Markdown while preventing code blocks and keeping layout
            details_safe = localize_decimals_in_text(formatted_details_text)
            details_prepared = _prepare_markdown_preserve_layout(details_safe)
            st.markdown(details_prepared)

        st.subheader(T("even_more_details_subheader"))
        with st.expander(T("even_more_details_expander")):
            formatted_more_details_text = T("even_more_details_text").format(**fmt_ctx)
            # Preserve Markdown formatting while avoiding code blocks and keeping layout
            safe_text = localize_decimals_in_text(formatted_more_details_text)
            prepared = _prepare_markdown_preserve_layout(safe_text)
            st.markdown(prepared)


def main() -> None:
    st.set_page_config(page_title="Digital CO2 Footprint", layout="centered")

    # Force French as default language before any translation
    if "lang" not in st.session_state:
        st.session_state["lang"] = "fr"
        set_language("fr")
    render_language_switch()
    page_title = T("page_title")
    st.markdown(
        f"<h1 style='text-align:center; font-size:2.5em; margin-bottom:0.2em'>{page_title}</h1>",
        unsafe_allow_html=True,
    )
    defaults = load_assumptions()
    assumptions = render_sidebar(defaults)

    # Center segmented control using columns, no label
    seg_options = ["producer", "consumer"]
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected = st.segmented_control(
            label="Role",
            options=[T(seg_options[0]), T(seg_options[1])],
            default=T(seg_options[0]),
            label_visibility="collapsed",
        )
    role = seg_options[0] if selected == T(seg_options[0]) else seg_options[1]
    render_page(role, assumptions)


if __name__ == "__main__":
    main()
