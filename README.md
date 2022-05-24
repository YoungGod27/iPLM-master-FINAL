# iPLM
An Integrated PLM Website

| [**View Code**](https://github.com/YoungGod27/iPLM-master-FINAL) |
|--------------------------------------------|

# Requirements
|  Install | Download links |
|--------------------------------------------|--------------------------------------------|
| Python 3.10.4 or higher | [Click here to downlod python](https://www.python.org/downloads/) |
| XAMPP Control Panel | [Click here to download xampp](https://www.apachefriends.org/download.html) |

# Setup
1. Run command prompt and change directory to project folder.
2. Install virtual environment
```cmd
pip install virtualenv
```
3. Create virtual environment
```cmd
python -m venv env
```
4. Activate virtual environment
```bash
if using bash: $ source ./env/Scripts/Activate
```
```cmd
if using cmd: env
```
5. Install dependencies
```cmd
pip install -r requirements.txt
```
6. Create database in phpmyadmin. DB_NAME = **iplmdatabase**
7. Make migrations
```cmd
python manage.py makemigrations
```
8. Migrate
```cmd
python manage.py migrate
```
9. Collect static files. After running command wait for a while then type **yes**
```cmd
py manage.py collectstatic
```
10. Create admin
```cmd
python manage.py createsuperuser
```
> Sample <br>
> Email: admin@plm.edu.ph <br>
> First name: Admin <br>
> Middle name: Admin <br>
> Last name: Admin <br>
> Password: Abc_1234 (note: this is not visible) <br>
> Password (again): Abc_1234 <br>

_Optional_
: **pwede mo lang ito magamit pag fresh pa ang database mo (walang laman)**
You can run `python manage.py databaseseed` to add users with default password of `password`

11. Run server
```cmd
run
```
12. Server address = 127.0.0.1:8000 or localhost:8000

# Usage
1. Run XAMPP Control Panel and make sure Apache & MySQL is running.
2. Run command prompt and change directory to project folder.
3. Activate virtual environment
```cmd
env
```
4. Run server
```cmd
run
```
