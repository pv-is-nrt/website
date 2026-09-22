"""Generate an ATS-friendly Resume (.docx) from the database, using a Word template.

Run from the project root:

    python manage.py generate_resume            # writes the .docx
    python manage.py generate_resume --pdf      # also converts to .pdf via Word

Everything reads from the local Django database (admin panel content), and the
output lands in base/static/base/docs/ where the site's download buttons point.
"""
import html as html_mod
import re
from itertools import groupby
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from docxtpl import DocxTemplate, Listing

from base.models import (
    Advising,
    BasicInformation,
    Education,
    Experience,
    HonorAndAward,
    Leadership,
    Mentoring,
    Presentation,
    Publication,
    Reference,
    SkillCategory,
)

TEMPLATE_PATH = Path("base/document_templates/resume_template_2.docx")
OUTPUT_DIR = Path("base/static/base/docs")
OUTPUT_NAME = "Prateek Verma - Resume"


def html_to_text(value, as_listing=False):
    """Convert admin-panel HTML (paragraphs, lists, <br>) into plain text.

    Conventions used here match docxtpl.Listing:
      - "\a" -> a full new paragraph
      - "\n" -> a soft line break inside the paragraph

    If as_listing=True, the output is intended for docxtpl.Listing which
    already handles \a as paragraph breaks and \n as soft breaks.
    If as_listing=False, \n is used for line breaks within the same paragraph.
    """
    if not value:
        return ""
    s = str(value)
    # Convert list items - use \n (soft break) for line breaks within same paragraph
    s = re.sub(r"<li[^>]*>", "\n\u2022 ", s, flags=re.I)          # bullet item on same para
    s = re.sub(r"</(?:p|div|li|ul|ol|h[1-6])>\r?\n?", "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_mod.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)                                  # collapse spaces
    if as_listing:
        s = re.sub(r"\a[ \t]*\a", "\a", s)                             # empty paragraphs
    s = re.sub(r"\n[ \t]*\n", "\n", s)                             # repeated breaks
    s = re.sub(r"^\n", "", s)                                         # strip leading newlines
    s = re.sub(r"\n$", "", s)                                         # strip trailing newlines
    return s.strip()


def listing(value):
    return Listing(html_to_text(value, as_listing=True))


def fmt_dates(start, end):
    start_year = start.year if start else None
    end_year = end.year if end else None
    if not start_year:
        return ""
    if start_year == end_year:
        return str(start_year)
    if not end_year:
        return f"{start_year}\u2013present"
    return f"{start_year}\u2013{end_year}"


class Command(BaseCommand):
    help = "Render the ATS-friendly Resume (.docx/.pdf) from the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pdf",
            action="store_true",
            help="Also export a PDF by converting the .docx with Microsoft Word.",
        )

    def handle(self, *args, **options):
        basic_info = BasicInformation.objects.get(pk=1)

        experiences = Experience.objects.order_by("-start_date")
        educations = Education.objects.order_by("-start_date")
        publications = Publication.objects.filter(featured=True).order_by("-date")
        presentations = Presentation.objects.filter(featured=True).order_by("-date")
        honors = HonorAndAward.objects.filter(featured=True).order_by("-start_date")
        leaderships = Leadership.objects.filter(featured=True).order_by("-start_date")
        references = Reference.objects.order_by("start_year")
        mentorings = Mentoring.objects.order_by("degree_type", "-start_date")
        advisings = Advising.objects.order_by("-start_date")
        skill_categories = SkillCategory.objects.filter(hidden=False).order_by("group", "order")
# ------- skills: a plain, keyword-friendly block of text -------
        skill_lines = []
        for category in skill_categories:
            names = [s.short_name or s.name for s in category.skill_set.all()]
            if names:
                skill_lines.append(f"{category.name}: {', '.join(names)}")
        skills_text = "\n".join(skill_lines) if skill_lines else ""

        # ------- mentoring / advising one-line summaries -------
        mentoring_counts = {
            degree: len(list(group))
            for degree, group in groupby(mentorings, key=lambda m: m.degree_type)
        }
        mentoring_part = ", ".join(
            f"{count} {degree.lower()}" for degree, count in mentoring_counts.items()
        )
        mentoring_summary = (
            f"Served as a mentor for Mentor Jackets, MSE Industry Mentoring and IITR "
            f"AMP for {mentoring_part} students."
        )
        count_direct_advising = len(Advising.objects.filter(name__endswith="*"))
        advising_summary = (
            f"Advised the research of {len(advisings)} members "
            f"({count_direct_advising} as direct supervisor) in areas such as "
            f"convolutional neural networks, machine learning for molecules, "
            f"linear and logistic regression, auxetics and metamaterials, "
            f"and structure-property relationships."
        )

        context = {
            "name": f"{basic_info.first_name} {basic_info.last_name}",
            "tagline": basic_info.resume_tagline or "",
            "work_email": basic_info.work_email or "",
            "website_url": basic_info.website_url or "",
            "phone": f"+{basic_info.country_phone_code} {basic_info.phone}".strip(),
            "resume_statement": listing(basic_info.resume_statement),
            "experiences": [
                {
                    "position": exp.position,
                    "organization": exp.organization.full_name if exp.organization else "",
                    "dates": fmt_dates(exp.start_date, exp.end_date),
                    "description": listing(exp.description),
                }
                for exp in experiences
            ],
            "educations": [
                {
                    "degree": edu.degree,
                    "major": edu.major,
                    "organization": edu.organization.full_name if edu.organization else "",
                    "dates": fmt_dates(edu.start_date, edu.end_date),
                    "gpa": str(edu.gpa),
                    "gpa_total": str(edu.gpa_total),
                }
                for edu in educations
            ],
            "skills": Listing(skills_text),
            "publications": [
                {
                    "authors": ", ".join(pub.authors_list_very_short()),
                    "year": str(pub.date.year),
                    "title": pub.title,
                    "publisher": pub.publisher,
                }
                for pub in publications
            ],
            "presentations": [
                {
                    "title": pres.title,
                    "venue": f"{pres.city}, {pres.country}",
                    "year": str(pres.date.year),
                }
                for pres in presentations
            ],
            "honors": [
                {
                    "title": hon.short_title or hon.title,
                    "organization": hon.organization.short_name if hon.organization else "",
                    "dates": fmt_dates(hon.start_date, hon.end_date),
                }
                for hon in honors
            ],
            "leaderships": [
                {
                    "title": lead.short_title or lead.title,
                    "organization": lead.organization.short_name if lead.organization else "",
                    "dates": fmt_dates(lead.start_date, lead.end_date),
                }
                for lead in leaderships
            ],
            "mentoring_summary": listing(mentoring_summary),
            "advising_summary": listing(advising_summary),
            "references": [
                {
                    "name": ref.name,
                    "title": ref.title,
                    "organization": ref.organization.short_name if ref.organization else "",
                    "email": ref.email,
                }
                for ref in references
            ],
            "extracurriculars": listing(basic_info.extra_curricular),
        }

        template_path = settings.BASE_DIR / TEMPLATE_PATH
        if not template_path.exists():
            raise CommandError(f"Resume template not found: {template_path}")

        output_dir = settings.BASE_DIR / OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        output_docx = output_dir / f"{OUTPUT_NAME}.docx"

        doc = DocxTemplate(str(template_path))
        doc.render(context)

        # Save the generated DOCX
        # Note: Avoid using & character in literal template text (headings, labels, etc.)
        # as docxtpl's fix_tables() method loses ampersand entities during lxml round-trip.
        # & characters inside data values (from the database context) are safe.
        doc.save(str(output_docx))
        self.stdout.write(self.style.SUCCESS(f"Wrote {output_docx}"))

        if options["pdf"]:
            from docx2pdf import convert

            output_pdf = output_docx.with_suffix(".pdf")
            convert(str(output_docx), str(output_pdf))
            self.stdout.write(self.style.SUCCESS(f"Wrote {output_pdf}"))