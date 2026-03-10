import unittest
from pathlib import Path

from resume_job_matcher import build_result, extract_experience_years, extract_salary, extract_skills, load_document_bytes


class ResumeMatcherTests(unittest.TestCase):
    def test_salary_extraction(self) -> None:
        self.assertEqual(extract_salary("Salary: 12 LPA"), "12 LPA")
        self.assertEqual(extract_salary("Global Comp\n$180,000 - $220,000 based on location"), "$180,000 - $220,000")

    def test_experience_extraction(self) -> None:
        self.assertEqual(extract_experience_years("Should have 7 years of strong hands-on experience", allow_date_fallback=False), 7)
        self.assertEqual(
            extract_experience_years(
                "Software Engineer\nJan 2021 - Present\nDeveloper\nJul 2018 - Dec 2020",
                allow_date_fallback=True,
            ),
            7.8,
        )

    def test_skill_extraction(self) -> None:
        skills = extract_skills("Python, React, Docker, Kubernetes, Jenkins, AWS")
        self.assertTrue({"Python", "React", "Docker", "Kubernetes", "Jenkins", "AWS"}.issubset(set(skills)))

    def test_build_result(self) -> None:
        resume_text = """
        John Doe
        Skills
        Python, Docker, Kubernetes, React
        Experience
        Jan 2020 - Present
        """
        jd_text = """
        Software Engineer
        Required Skills
        Python
        Docker
        Kafka
        """
        result = build_result(resume_text, [("JD001", "software_engineer.txt", jd_text)])
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["matchingJobs"][0]["matchingScore"], 66.7)

    def test_load_document_bytes_for_text_upload(self) -> None:
        sample_text = Path("sample_resume.txt").read_bytes()
        parsed = load_document_bytes("sample_resume.txt", sample_text)
        self.assertIn("John Doe", parsed)
        self.assertIn("Spring Boot", parsed)


if __name__ == "__main__":
    unittest.main()
