from django.db import migrations, models


CATEGORIES = [
    (
        'Artificial Intelligence & Machine Learning',
        'Deep Learning, Large Language Models (LLMs), Vision-Language Models (VLMs), Foundation Models, Transfer Learning, Fine-Tuning, Few-Shot Learning, Zero-Shot Learning, Model Evaluation, Agentic AI, Convolutional Neural Networks (CNNs), ResNet, Generative Adversarial Networks (GANs), Support Vector Machines (SVMs), Clustering, Logistic Regression, Linear Regression',
        'Deep Learning, Large Language Models (LLMs), Vision-Language Models (VLMs), Fine-Tuning, Convolutional Neural Networks (CNNs), Generative Adversarial Networks (GANs), Model Evaluation',
    ),
    (
        'Scientific AI',
        'Multimodal Learning, Multi-Omics, Biomedical Image Analysis, Microscopy Image Analysis, Materials Informatics, Chemical Informatics, Bio-informatics, Molecular/Polymer Property Prediction, Molecular Parsing, Computational Ethology, Inverse Design, Object Detection & Tracking, Animal Behavior Classification',
        'Multimodal Learning, Biomedical Image Analysis, Materials Informatics, Molecular/Polymer Property Prediction, Computational Ethology, Inverse Design',
    ),
    (
        'Data Analysis',
        'Statistical Programming & Analysis, Data Mining, ML Pipelines, Preprocessing, Feature Engineering, Dimensionality Reduction, Data Visualization, Cross-Validation, Error Analysis',
        'Statistical Programming & Analysis, Data Mining, Feature Engineering, Data Visualization, Cross-Validation, Error Analysis',
    ),
    (
        'Computer Vision & Image Analysis',
        'Image Classification, Segmentation, Counting, Tracking, Video Analysis, Pose Estimation, Image-Based Phenotyping, Vision-Language Modeling, Visual Question Answering (VQA), Image Annotation, Pillow, Fiji/ImageJ, Cellpose, Cellpose-SAM, Segment Anything Model (SAM), LLaVA, Hugging Face Transformers, OpenCV, napari, scikit-image, DeepLabCut, SLEAP',
        'Image Classification, Segmentation, Object Detection & Tracking, Pose Estimation, Image-Based Phenotyping, Visual Question Answering (VQA), Segment Anything Model (SAM), OpenCV, DeepLabCut, SLEAP',
    ),
    (
        'Programming & Computational Tools',
        'Python, MATLAB, PHP, SQL, C/C++, BioPython, Django, RDKit, Pandas, NumPy, TensorFlow, PyTorch, scikit-learn, Matplotlib, Pillow, MySQL, LAMMPS, Hugging Face Transformers, OpenCV, SciPy, Seaborn, Jupyter/JupyterLab, Git/GitHub, FastAPI, Streamlit, Gradio, OpenAI API, Anthropic API, Gemini API',
        'Python, MATLAB, C/C++, SQL, TensorFlow, PyTorch, scikit-learn, Hugging Face Transformers, OpenCV, Pandas, NumPy, Git/GitHub',
    ),
    (
        'Computing & Research Infrastructure',
        'High-Performance Computing (HPC), GPU Computing, Cloud Computing, Amazon Web Services (AWS), Data Pipelines, ML Workflows & Frameworks, Data Infrastructure, Dashboards, Containerization, Docker, Linux, Bash/Shell Scripting, Version Control, Database Design',
        'High-Performance Computing (HPC), GPU Computing, Cloud Computing, Amazon Web Services (AWS), Data Pipelines, Docker, Linux, Version Control',
    ),
    (
        'Materials & Chemical Science',
        'Polymer Science, Polyurethane Synthesis, Liquid Crystals, Liquid-Crystal Elastomer (LCE) Synthesis, Free-Radical Polymerization, Silanes & Silicones, Polymer Processing, Viscoelasticity, Auxetic Materials, Metamaterials, Biopolymers, Nanotechnology, Materials Characterization, Structure-Property Relationships, Thermal Analysis, Chemical Formulation, Molecular Modeling, Computational Chemistry, Polymer Chemistry, Polymer Networks, Materials Design',
        'Polymer Science, Polyurethane Synthesis, Liquid-Crystal Elastomer (LCE) Synthesis, Polymer Processing, Viscoelasticity, Materials Characterization, Polymer Chemistry, Materials Design',
    ),
    (
        'Industrial R&D',
        'Protective Coatings, Adhesives, Process Development, Product Development, Chemical Mixing, Chemical Formulations, Thermal & UV Curing, Slot-Die Coating, Bar Coating, Process Optimization, Manufacturing Scale-Up, Quality Control, Technical Project Management, Research-to-Production Translation',
        'Protective Coatings, Adhesives, Process Development, Product Development, Thermal & UV Curing, Manufacturing Scale-Up, Quality Control',
    ),
    (
        'Experimental Methods & Characterization',
        'Isothermal Titration Calorimetry (ITC), Environmental Testing, Electron Microscopy, Scanning Electron Microscopy (SEM), Fourier-Transform Infrared Spectroscopy (FTIR), Micro-Computed Tomography (Micro-CT), Viscometry, Atomic Force Microscopy (AFM), Differential Scanning Calorimetry (DSC), Thermogravimetric Analysis (TGA), Dynamic Mechanical Analysis (DMA), Mechanical Testing, Thermal Analysis, Materials Characterization, Rheology, Spectroscopy, Microscopy, Polymer Characterization, Coating Characterization',
        'Isothermal Titration Calorimetry (ITC), Electron Microscopy, Fourier-Transform Infrared Spectroscopy (FTIR), Micro-Computed Tomography (Micro-CT), Atomic Force Microscopy (AFM), Differential Scanning Calorimetry (DSC), Dynamic Mechanical Analysis (DMA), Rheology, Spectroscopy',
    ),
    (
        'Interpersonal',
        'Mentoring, Research Advising & Training, Leadership, Team Building, Diversity, Equity & Inclusion (DEI), Scientific Illustration, Interdisciplinary Collaboration, Scientific Communication, Workshop Development & Delivery, Stakeholder Engagement',
        'Mentoring, Research Advising & Training, Leadership, Diversity, Equity & Inclusion (DEI), Interdisciplinary Collaboration, Scientific Communication, Stakeholder Engagement',
    ),
]


def replace_skill_categories(apps, schema_editor):
    SkillCategory = apps.get_model('base', 'SkillCategory')
    database = schema_editor.connection.alias
    categories = SkillCategory.objects.using(database)
    categories.all().delete()
    for name, skills, skills_short in CATEGORIES:
        categories.create(
            name=name,
            score=50,
            group='1',
            order=1,
            hidden=False,
            skills=skills,
            skills_short=skills_short,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0094_skill_single_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillcategory',
            name='skills',
            field=models.TextField(default='', verbose_name='Skills (CV and website)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='skillcategory',
            name='skills_short',
            field=models.TextField(default='', verbose_name='Skills (resume)'),
            preserve_default=False,
        ),
        migrations.DeleteModel(name='Skill'),
        migrations.RunPython(replace_skill_categories),
        migrations.RemoveField(
            model_name='skillcategory',
            name='score',
        ),
        migrations.RemoveField(
            model_name='skillcategory',
            name='group',
        ),
        migrations.RemoveField(
            model_name='skillcategory',
            name='order',
        ),
        migrations.RemoveField(
            model_name='skillcategory',
            name='hidden',
        ),
    ]