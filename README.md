# Resume Parsing and Job Matching System

Rule-based resume parsing and job matching implementation built without LLMs or AI parsing APIs.

## What it does

- Extracts `name`, `salary`, `yearOfExperience`, and `resumeSkills` from a resume.
- Extracts `role`, `aboutRole`, `salary`, `yearOfExperience`, `requiredSkills`, and `optionalSkills` from each JD.
- Builds a `skillsAnalysis` array that marks every JD skill as present or absent in the resume.
- Computes `matchingScore = matched_jd_skills / total_jd_skills * 100`.

## Approach

- Text extraction:
  - `.txt` and `.md` via standard file reads
  - `.docx` via XML extraction from the document archive
  - `.pdf` via `pdfplumber`, `PyMuPDF (fitz)`, or `PyPDF2` if available
- Salary extraction:
  - Regex for labeled compensation lines, currency ranges, and `LPA` formats
- Experience extraction:
  - Regex for explicit year mentions
  - Date-range fallback for resumes such as `Jan 2022 - Present`
- Skill extraction:
  - Canonical rule-based skill dictionary with aliases
  - Section-aware extraction for required vs optional JD skills
  - Short-phrase fallback extraction for bullet items not covered by the dictionary

## Files

- [1.py](/d:/python/1.py): CLI entrypoint
- [resume_job_matcher.py](/d:/python/resume_job_matcher.py): extraction and matching logic
- [streamlit_app.py](/d:/python/streamlit_app.py): Streamlit frontend for resume upload and job matching
- [test_resume_job_matcher.py](/d:/python/test_resume_job_matcher.py): unit tests
- [requirements.txt](/d:/python/requirements.txt): dependencies for local Streamlit deployment
- [sample_resume.txt](/d:/python/sample_resume.txt): bundled sample resume
- [sample_jd_astra.txt](/d:/python/sample_jd_astra.txt): bundled sample JD
- [sample_jd_capgemini.txt](/d:/python/sample_jd_capgemini.txt): bundled sample JD

## Usage

Run the bundled demo:

```bash
python 1.py --demo
```

Run on your own files:

```bash
python 1.py --resume resume.pdf --jd jd1.txt --jd jd2.txt
python 1.py --resume resume.docx --jd-dir ./jds --output sample_output.json
```

Run tests:

```bash
python -m unittest test_resume_job_matcher.py
```

## Streamlit

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit app locally:

```bash
streamlit run streamlit_app.py
```

The app supports:

- bundled demo mode using the sample resume and sample JDs
- uploading one resume file and multiple JD files
- JSON download of the final matching result

## Stable deployment

Recommended target: Streamlit Community Cloud

- Repository: `Sritankar/Resume-llm-parser`
- Branch: `main`
- Main file path: `streamlit_app.py`

Deployment steps:

1. Sign in at `https://share.streamlit.io/`
2. Click `Create app`
3. Select the repository above
4. Set the main file path to `streamlit_app.py`
5. Click `Deploy`

## Output shape

```json
{
  "name": "John Doe",
  "salary": "18 LPA",
  "yearOfExperience": 7.8,
  "resumeSkills": ["Python", "Java", "Spring Boot"],
  "matchingJobs": [
    {
      "jobId": "JD001",
      "role": "Software Engineer",
      "aboutRole": "Build systems that support rocket testing and launch operations.",
      "skillsAnalysis": [
        { "skill": "Python", "presentInResume": true },
        { "skill": "gRPC", "presentInResume": false }
      ],
      "matchingScore": 83
    }
  ]
}
```
