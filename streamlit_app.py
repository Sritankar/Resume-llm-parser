from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from resume_job_matcher import build_result, demo_paths, load_document, load_document_bytes


SUPPORTED_TYPES = ["txt", "md", "pdf", "docx"]


def load_demo_payload() -> tuple[str, list[tuple[str, str, str]]]:
    resume_path, jd_paths = demo_paths()
    resume_text = load_document(resume_path)
    jobs = [(f"JD{index:03d}", path.name, load_document(path)) for index, path in enumerate(jd_paths, start=1)]
    return resume_text, jobs


def load_uploaded_payload(
    resume_file: st.runtime.uploaded_file_manager.UploadedFile | None,
    jd_files: list[st.runtime.uploaded_file_manager.UploadedFile],
) -> tuple[str, list[tuple[str, str, str]]]:
    if resume_file is None:
        raise ValueError("Upload one resume file.")
    if not jd_files:
        raise ValueError("Upload at least one job description file.")

    resume_text = load_document_bytes(resume_file.name, resume_file.getvalue())
    jobs = [
        (f"JD{index:03d}", uploaded.name, load_document_bytes(uploaded.name, uploaded.getvalue()))
        for index, uploaded in enumerate(jd_files, start=1)
    ]
    return resume_text, jobs


def render_resume_summary(result: dict[str, object]) -> None:
    st.subheader("Resume Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Candidate", str(result.get("name") or "Not found"))
    col2.metric("Salary", str(result.get("salary") or "Not found"))
    col3.metric("Experience", str(result.get("yearOfExperience") or "Not found"))
    st.write("**Resume skills**")
    skills = result.get("resumeSkills", [])
    if skills:
        st.write(", ".join(str(skill) for skill in skills))
    else:
        st.write("No resume skills detected.")


def render_job_matches(result: dict[str, object]) -> None:
    st.subheader("Matching Jobs")
    jobs = result.get("matchingJobs", [])
    if not jobs:
        st.info("No job descriptions were matched.")
        return

    for index, job in enumerate(jobs, start=1):
        title = f"{index}. {job['jobId']} | {job['role']} | Score: {job['matchingScore']}"
        with st.expander(title, expanded=index == 1):
            meta1, meta2, meta3 = st.columns(3)
            meta1.metric("Matching Score", str(job["matchingScore"]))
            meta2.metric("JD Salary", str(job.get("salary") or "Not found"))
            meta3.metric("JD Experience", str(job.get("yearOfExperience") or "Not found"))
            st.write("**About role**")
            st.write(str(job.get("aboutRole") or ""))
            st.write("**Required skills**")
            st.write(", ".join(job.get("requiredSkills", [])) or "None")
            st.write("**Optional skills**")
            st.write(", ".join(job.get("optionalSkills", [])) or "None")
            st.write("**Skill analysis**")
            st.dataframe(job.get("skillsAnalysis", []), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Resume Matcher", page_icon="R", layout="wide")
    st.title("Resume Parsing and Job Matching")
    st.caption("Rule-based parser and matcher. No LLMs, no AI parsing APIs.")

    with st.sidebar:
        st.header("Input")
        use_demo = st.toggle("Use bundled demo files", value=False)
        st.caption("Demo mode loads the sample resume and sample JDs already in the project.")

    resume_file = None
    jd_files: list[st.runtime.uploaded_file_manager.UploadedFile] = []

    if not use_demo:
        left, right = st.columns(2)
        with left:
            resume_file = st.file_uploader("Upload resume", type=SUPPORTED_TYPES, accept_multiple_files=False)
        with right:
            jd_files = st.file_uploader("Upload job descriptions", type=SUPPORTED_TYPES, accept_multiple_files=True)

    run_clicked = st.button("Run matching", type="primary", use_container_width=True)

    if use_demo:
        sample_resume_path, sample_jd_paths = demo_paths()
        st.info(
            f"Demo files: resume `{Path(sample_resume_path).name}` and "
            f"{', '.join(path.name for path in sample_jd_paths)}"
        )

    if not run_clicked:
        st.write("Upload files or enable demo mode, then run matching.")
        return

    try:
        if use_demo:
            resume_text, jobs = load_demo_payload()
        else:
            resume_text, jobs = load_uploaded_payload(resume_file, jd_files)
        result = build_result(resume_text, jobs)
    except Exception as exc:
        st.error(str(exc))
        return

    render_resume_summary(result)
    render_job_matches(result)

    st.subheader("Output JSON")
    payload = json.dumps(result, indent=2)
    st.code(payload, language="json")
    st.download_button(
        "Download JSON",
        data=payload,
        file_name="resume_match_output.json",
        mime="application/json",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
