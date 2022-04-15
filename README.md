# Prateek's website

Hi! If you haven't looked at the actual website, it's hosted at [prateekverma.com](https://prateekverma.com).

# Description
The following tech was used to build this website:
1. Backend: Django (a Python framework)
2. Frontend: HTML/CSS and a tiny bit of JavaScript
This website has several Django apps. At the time of writing, there was a `base` and a `blog` app.

# Table of contents
Not applicable.

# How to install and use the project
You must install Django on your machine first. I strongly recommend learning Django first, before attempting to use this code. If you know Django, know that the following critical files/folders are not included in the repository, but will be essential for you to try the code on you machine:
- A `/media` folder to hold images that were uploaded via forms. The contents of this folder are user generated, hence not a part of the code.
- A database - at the time of writing, SQLITE3 is being used, but the data file is not included in the repository. *However*, all migration files that will help you recreate the database at your end are provided. I think you'll still have to input your own data after the database is constructed. You can check the `/djangosite/settings.py` file to see what kind database is being used at the time of reading.
- A configuration file - to hold and provide sensitive information, such as the SECRET_KEY, EMAIL_PASSWORD etc. to the Django apps. You will have to create one on your own machine: `/djangosite/settings.py` is one such file that imports sensitive information from the config file.

# License
If you like the website or the code, feel free to use it for your own projects or for learning: I'd appreciate acknowledgement though. If you do use it, I'd love to hear from you and also any questions you may have.

# Credits
Many thanks to the YouTube channels of Corey Schafer and Dennis Ivy for their tutorials on Django and Python. And the best of all, the official Django documentation.

# How to contribute
This is not an open source project. But if you have any cool ideas, kindly contact me!

# Tests
Code for testing application: None.

# Contact
A good way to get in touch with me is through my website's contact page.

That's all! Thanks for visiting.