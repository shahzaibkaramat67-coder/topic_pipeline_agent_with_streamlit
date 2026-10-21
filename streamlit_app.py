import asyncio
import json
import os

import streamlit as st
from openai import OpenAIError

from model import (
    ModelSettings,
    model_session,
    test_api_connection,
    validate_settings,
)
from pipeline import pipeline


st.set_page_config(
    page_title="Topic Studio",
    page_icon=":material/article:",
    layout="wide",
)

st.session_state.setdefault("api_settings", None)
st.session_state.setdefault("generated_article", "")
st.session_state.setdefault("generated_topic", "")
st.session_state.setdefault(
    "api_base_url_input",
    os.getenv("FREELLMAPI_BASE_URL", "https://api.openai.com/v1"),
)
st.session_state.setdefault(
    "api_model_input", os.getenv("FREELLMAPI_MODEL", "gpt-4o-mini")
)
st.session_state.setdefault(
    "api_key_input", os.getenv("FREELLMAPI_API_KEY", "")
)


def _safe_error(error: Exception, settings: ModelSettings) -> str:
    message = str(error)
    if settings.api_key:
        message = message.replace(settings.api_key, "[hidden]")
    return message


with st.sidebar:
    st.title("Topic Studio")
    st.caption("Configure an OpenAI-compatible API for your session.")

    with st.form("api_settings_form"):
        st.text_input(
            "API base URL",
            key="api_base_url_input",
            placeholder="https://api.openai.com/v1",
            help="Use the provider's OpenAI-compatible API endpoint.",
        )
        st.text_input(
            "Model",
            key="api_model_input",
            placeholder="gpt-4o-mini",
        )
        st.text_input(
            "API key",
            key="api_key_input",
            type="password",
            help="Kept only in this browser session; it is not saved to a file.",
        )
        save_settings = st.form_submit_button(
            "Save API settings", type="primary", width="stretch"
        )

    if save_settings:
        settings = ModelSettings(
            base_url=st.session_state.api_base_url_input.strip(),
            model=st.session_state.api_model_input.strip(),
            api_key=st.session_state.api_key_input.strip(),
        )
        try:
            validate_settings(settings)
        except ValueError as error:
            st.session_state.api_settings = None
            st.error(str(error))
        else:
            st.session_state.api_settings = settings
            st.success("Settings saved for this session.")

    saved_settings = st.session_state.api_settings
    if saved_settings is not None:
        if st.button(
            "Test API connection",
            icon=":material/lan:",
            width="stretch",
        ):
            try:
                with st.spinner("Checking your API connection..."):
                    reply = asyncio.run(test_api_connection(saved_settings))
                st.success("API connection succeeded.")
                if reply.strip():
                    st.caption(f"Model reply: {reply.strip()}")
            except (OpenAIError, ValueError) as error:
                st.error(f"API test failed: {_safe_error(error, saved_settings)}")
    else:
        st.caption("Save your API settings to test the connection.")

    st.caption("Settings are isolated per browser session and are not persisted.")


st.title("Turn a topic into a polished article")
st.write(
    "Build an outline, review its quality, write the article, and polish the final draft."
)

topic = st.text_area(
    "What would you like to write about?",
    placeholder="For example: How community gardens improve urban neighborhoods",
    height=140,
)

generate = st.button(
    "Generate article",
    type="primary",
    icon=":material/auto_awesome:",
    disabled=st.session_state.api_settings is None,
)

if st.session_state.api_settings is None:
    st.info("Add and save your API details in the sidebar before generating.")
elif generate:
    if not topic.strip():
        st.warning("Enter a topic before generating an article.")
    else:
        settings = st.session_state.api_settings

        try:
            with st.status(
                "Starting article generation...",
                expanded=True,
            ) as progress_status:
                def report_progress(message: str) -> None:
                    progress_status.update(
                        label=message,
                        state="running",
                        expanded=True,
                    )
                    progress_status.write(f"• {message}")

                async def _generate_article() -> str:
                    async with model_session(settings):
                        return await pipeline(
                            topic.strip(),
                            on_progress=report_progress,
                        )

                article = asyncio.run(_generate_article())
                progress_status.update(
                    label="Article generated successfully",
                    state="running",
                    expanded=True,
                )
            st.session_state.generated_article = article
            st.session_state.generated_topic = topic.strip()
        except (OpenAIError, ValueError, json.JSONDecodeError) as error:
            st.error(f"Article generation failed: {_safe_error(error, settings)}")

if st.session_state.generated_article:
    st.subheader("Your article")
    st.caption(f"Topic: {st.session_state.generated_topic}")
    with st.container(border=True):
        st.markdown(st.session_state.generated_article)
    st.download_button(
        "Download article",
        data=st.session_state.generated_article,
        file_name="article.md",
        mime="text/markdown",
        icon=":material/download:",
    )
