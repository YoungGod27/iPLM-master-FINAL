# iPLM-master-FINAL-fork

## How to install

**1 Create virtual environment**
`python -m venv env`

**2 Activate virtual env.**
Bash : `$ source ./env/Scripts/Activate`
CMD : `env\Scripts\Activate.bat`

**3 Install dependencies**
`pip install -r requirements.txt`

**4 create database in phpmyadmin**
DB_NAME = **iplmdatabase**

**5 Make Migrations**
`python manage.py makemigrations`

**6 Migrate**
`python manage.py migrate`

**7 Statics**
`py manage.py collectstatic` then type `yes`

**8 Create Admin**
`python manage.py createsuperuser`

> Sample <br>
> Email: admin@plm.edu.ph <br>
> First name: Admin <br>
> Middle name: Admin <br>
> Last name: Admin <br>
> Password: Abc_1234 (Type lang kayo kahit di visible) <br>
> Password (again): Abc_1234 <br>

_Optional_
**NOTE: Pwede mo lang ito magamit pag fresh pa ang database mo (Walang laman)**
You can run `python manage.py databaseseed` to add users with default password of `password`

**9 Runserver**
`python manage.py runserver` then **Ctrl+click 127.0.0.1:8000**
