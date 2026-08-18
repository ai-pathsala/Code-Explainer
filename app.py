"""
Code Tutor Bot — an AI chatbot that teaches code line by line.

Upload a file or paste code, pick your experience level and explanation
language, and the bot walks you through it — plus complexity analysis,
bug/improvement review, a quiz to test what you learned, and a follow-up
Q&A chat grounded in your actual code.
"""

import streamlit as st
from llm_client import chat_completion, chat_completion_json, active_provider_info, LLMError
from utils import detect_language, chunk_code, build_markdown_report

st.set_page_config(page_title="Code Tutor Bot", page_icon="🧑‍🏫", layout="wide")

# ----------------------------------------------------------------------
# Session state initialisation
# ----------------------------------------------------------------------
defaults = {
    "code": "",
    "filename": "pasted_code.txt",
    "language": "text",
    "line_blocks": [],
    "current_step": 0,
    "chat_history": [],
    "complexity_text": "",
    "bugs_text": "",
    "quiz": [],
    "quiz_answers": {},
    "quiz_submitted": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ----------------------------------------------------------------------
# Sidebar — input + settings
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("🧑‍🏫 Code Tutor Bot")
    info = active_provider_info()
    key_status = "✅ key loaded" if info["key_present"] else "⚠️ key missing — check .env"
    st.caption(f"Provider: **{info['provider']}** · Model: `{info['model']}` · {key_status}")

    st.divider()
    st.subheader("1. Give me some code")
    uploaded = st.file_uploader(
        "Upload a code file",
        type=list(k.strip(".") for k in [
            "py", "js", "jsx", "ts", "tsx", "java", "c", "h", "cpp", "hpp", "cs",
            "go", "rs", "rb", "php", "html", "css", "sql", "sh", "kt", "swift",
            "r", "m", "scala", "json", "yaml", "yml", "dart", "lua", "pl", "txt",
        ]),
    )
    pasted = st.text_area("...or paste code here", height=200, placeholder="def hello():\n    print('hi')")

    if uploaded is not None:
        st.session_state.code = uploaded.read().decode("utf-8", errors="replace")
        st.session_state.filename = uploaded.name
        st.session_state.language = detect_language(uploaded.name)
    elif pasted.strip():
        st.session_state.code = pasted
        st.session_state.filename = "pasted_code.txt"
        st.session_state.language = "text"

    st.divider()
    st.subheader("2. Teach me how")
    level = st.select_slider(
        "Experience level",
        options=["Absolute Beginner", "Beginner", "Intermediate", "Advanced"],
        value="Beginner",
    )
    resp_language = st.radio("Explain in", ["English", "Bengali (বাংলা)", "Both"], horizontal=True)
    chunk_size = st.slider("Lines per explanation block (max)", 5, 50, 20)

    if st.button("🔄 Reset everything", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

if not st.session_state.code.strip():
    st.info("👈 Upload a file or paste code in the sidebar to get started.")
    st.markdown(
        """
        ### What this bot does
        - **Line-by-line teaching** — walks through your code like a patient tutor, step by step
        - **Complexity analysis** — time/space Big-O for the key functions
        - **Bug & improvement review** — prioritized, actionable feedback
        - **Quiz mode** — checks whether the explanation actually landed
        - **Follow-up chat** — ask anything about the code you uploaded
        - Explanations in **English, Bengali, or both**
        - Export the whole session as a **Markdown report**
        """
    )
    st.stop()

code = st.session_state.code
language = st.session_state.language
filename = st.session_state.filename

st.subheader(f"📄 `{filename}`  ·  detected language: `{language}`")
with st.expander("View full source", expanded=False):
    st.code(code, language=language, line_numbers=True)


def lang_instruction():
    if resp_language == "English":
        return "Respond entirely in English."
    elif resp_language.startswith("Bengali"):
        return "Respond entirely in Bengali (বাংলা), using Latin technical terms (variable, function, loop, etc.) where that's clearer."
    else:
        return "Respond in English first, then give a short Bengali (বাংলা) summary of the same explanation."


tabs = st.tabs(["📖 Line-by-Line", "⏱️ Complexity", "🐛 Bugs & Improvements", "🧠 Quiz Me", "💬 Ask Questions", "📥 Export"])

# ----------------------------------------------------------------------
# TAB 1: Line-by-line teaching, step-through style
# ----------------------------------------------------------------------
with tabs[0]:
    st.write("Breaks your code into logical blocks and explains each one, tutor-style.")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        generate = st.button("✨ Generate line-by-line explanation", type="primary")
    with col_b:
        show_all = st.toggle("Show all blocks at once (instead of step-through)", value=False)

    if generate:
        numbered_lines = code.splitlines()
        chunks = chunk_code(code, chunk_size=chunk_size)
        all_blocks = []
        progress = st.progress(0.0, text="Explaining your code...")
        for idx, (start, end, chunk_text) in enumerate(chunks):
            numbered = "\n".join(f"{start + i}: {ln}" for i, ln in enumerate(chunk_text.splitlines()))
            system = (
                "You are an expert, encouraging programming tutor. You explain code precisely, "
                "one logical statement at a time, calibrated to the learner's stated level. "
                f"Learner level: {level}. {lang_instruction()}"
            )
            user = f"""Explain the following {language} code, which is lines {start}-{end} of a larger file.
Each shown line is prefixed with its real line number — use those exact numbers in your output.

```
{numbered}
```

Return ONLY a JSON object: {{"blocks": [{{"start_line": int, "end_line": int, "code": "exact code for these lines, no line-number prefixes", "explanation": "clear tutor-style explanation"}}]}}
Group tightly related lines into one block (e.g. a function signature, an if/else, a small loop body) rather than one block per physical line, but never merge more than 5 lines into a single block. Cover every line in the range."""
            try:
                result = chat_completion_json(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}]
                )
                all_blocks.extend(result.get("blocks", []))
            except LLMError as e:
                st.error(f"Error explaining lines {start}-{end}: {e}")
                break
            progress.progress((idx + 1) / len(chunks), text=f"Explained lines {start}-{end}...")
        progress.empty()
        st.session_state.line_blocks = all_blocks
        st.session_state.current_step = 0

    blocks = st.session_state.line_blocks
    if blocks:
        if show_all:
            for b in blocks:
                label = f"Lines {b.get('start_line')}-{b.get('end_line')}" if b.get('start_line') != b.get('end_line') else f"Line {b.get('start_line')}"
                st.markdown(f"**{label}**")
                st.code(b.get("code", ""), language=language)
                st.markdown(b.get("explanation", ""))
                st.divider()
        else:
            step = st.session_state.current_step
            step = max(0, min(step, len(blocks) - 1))
            st.session_state.current_step = step
            b = blocks[step]

            st.progress((step + 1) / len(blocks), text=f"Block {step + 1} of {len(blocks)}")
            label = f"Lines {b.get('start_line')}-{b.get('end_line')}" if b.get('start_line') != b.get('end_line') else f"Line {b.get('start_line')}"
            st.markdown(f"### {label}")
            st.code(b.get("code", ""), language=language)
            st.info(b.get("explanation", ""))

            nav1, nav2, nav3 = st.columns([1, 1, 4])
            with nav1:
                if st.button("⬅️ Previous", disabled=step == 0, use_container_width=True):
                    st.session_state.current_step = step - 1
                    st.rerun()
            with nav2:
                if st.button("Next ➡️", disabled=step == len(blocks) - 1, use_container_width=True):
                    st.session_state.current_step = step + 1
                    st.rerun()
    else:
        st.caption("Click **Generate line-by-line explanation** to begin.")

# ----------------------------------------------------------------------
# TAB 2: Complexity analysis
# ----------------------------------------------------------------------
with tabs[1]:
    st.write("Estimates time and space complexity for the key functions/algorithms.")
    if st.button("⏱️ Analyze complexity"):
        system = f"You are an expert algorithms tutor. Level: {level}. {lang_instruction()}"
        user = f"""Analyze the time and space complexity of the significant functions/algorithms in this {language} code.
For each significant function, give Big-O notation for time and space, with a short justification tied to the actual loops/recursion/data structures used.
If the code has no meaningful algorithmic complexity (e.g. pure config), say so briefly.

```{language}
{code}
```"""
        try:
            with st.spinner("Analyzing..."):
                st.session_state.complexity_text = chat_completion(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}]
                )
        except LLMError as e:
            st.error(str(e))

    if st.session_state.complexity_text:
        st.markdown(st.session_state.complexity_text)

# ----------------------------------------------------------------------
# TAB 3: Bug / improvement review
# ----------------------------------------------------------------------
with tabs[2]:
    st.write("Reviews the code for bugs, edge cases, and quality improvements.")
    if st.button("🐛 Review code"):
        system = f"You are a meticulous senior code reviewer, direct but constructive. Level of learner: {level}. {lang_instruction()}"
        user = f"""Review this {language} code for bugs, missed edge cases, and code-quality improvements.
Return a prioritized list grouped as Critical / Moderate / Minor. For each item: what the issue is, why it matters, and a concrete suggested fix.
If the code is genuinely solid, say so honestly rather than inventing issues.

```{language}
{code}
```"""
        try:
            with st.spinner("Reviewing..."):
                st.session_state.bugs_text = chat_completion(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}]
                )
        except LLMError as e:
            st.error(str(e))

    if st.session_state.bugs_text:
        st.markdown(st.session_state.bugs_text)

# ----------------------------------------------------------------------
# TAB 4: Quiz mode
# ----------------------------------------------------------------------
with tabs[3]:
    st.write("Tests whether the explanation actually stuck — answer a few questions about your code.")
    n_questions = st.slider("Number of questions", 3, 8, 5)
    if st.button("🧠 Generate quiz"):
        system = f"You are a friendly but rigorous programming tutor writing a comprehension quiz. Level: {level}. {lang_instruction()}"
        user = f"""Write {n_questions} quiz questions that test understanding of this {language} code — what it does, why it's written this way, and what would happen under different inputs.
Mix multiple-choice and short-answer questions.
Return ONLY JSON: {{"questions": [{{"question": str, "type": "mcq" or "short", "options": [str, ...] (only if mcq, 3-4 options), "correct_answer": str, "explanation": str}}]}}

```{language}
{code}
```"""
        try:
            with st.spinner("Writing quiz..."):
                result = chat_completion_json(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}]
                )
            st.session_state.quiz = result.get("questions", [])
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
        except LLMError as e:
            st.error(str(e))

    quiz = st.session_state.quiz
    if quiz:
        with st.form("quiz_form"):
            for i, q in enumerate(quiz):
                st.markdown(f"**Q{i + 1}. {q.get('question', '')}**")
                if q.get("type") == "mcq" and q.get("options"):
                    st.session_state.quiz_answers[i] = st.radio(
                        f"answer_{i}", q["options"], key=f"quiz_{i}", label_visibility="collapsed"
                    )
                else:
                    st.session_state.quiz_answers[i] = st.text_input(
                        f"answer_{i}", key=f"quiz_{i}", label_visibility="collapsed"
                    )
            submitted = st.form_submit_button("Submit answers")
            if submitted:
                st.session_state.quiz_submitted = True

        if st.session_state.quiz_submitted:
            score = 0
            for i, q in enumerate(quiz):
                user_ans = str(st.session_state.quiz_answers.get(i, "")).strip().lower()
                correct = str(q.get("correct_answer", "")).strip().lower()
                is_correct = user_ans == correct or (q.get("type") != "mcq" and correct in user_ans)
                score += int(is_correct)
                if is_correct:
                    st.success(f"Q{i + 1}: Correct! 🎉  {q.get('explanation', '')}")
                else:
                    st.error(f"Q{i + 1}: Not quite. Correct answer: **{q.get('correct_answer')}**.  {q.get('explanation', '')}")
            st.metric("Score", f"{score} / {len(quiz)}")
    else:
        st.caption("Click **Generate quiz** after reading the explanation.")

# ----------------------------------------------------------------------
# TAB 5: Follow-up chat, grounded in the code
# ----------------------------------------------------------------------
with tabs[4]:
    st.write("Ask anything about the uploaded code — it remembers the code and your conversation.")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("e.g. Why is a dictionary used here instead of a list?")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        system = (
            f"You are a helpful programming tutor. The learner is discussing the following {language} code "
            f"with you. Answer only using this code as context; if the question is unrelated, say so. "
            f"Level: {level}. {lang_instruction()}\n\n```{language}\n{code}\n```"
        )
        api_messages = [{"role": "system", "content": system}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history
        ]
        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = chat_completion(api_messages, temperature=0.4)
                st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
        except LLMError as e:
            st.error(str(e))

# ----------------------------------------------------------------------
# TAB 6: Export everything as a Markdown report
# ----------------------------------------------------------------------
with tabs[5]:
    st.write("Bundle the line-by-line explanation, complexity analysis, and bug review into one file.")
    if not st.session_state.line_blocks:
        st.caption("Generate at least the line-by-line explanation first (Tab 1).")
    else:
        report = build_markdown_report(
            filename=filename,
            language=language,
            code=code,
            line_explanations=st.session_state.line_blocks,
            complexity=st.session_state.complexity_text or None,
            bugs=st.session_state.bugs_text or None,
        )
        st.download_button(
            "📥 Download Markdown report",
            data=report,
            file_name=f"{filename}_explained.md",
            mime="text/markdown",
            use_container_width=True,
        )
        with st.expander("Preview"):
            st.markdown(report)
