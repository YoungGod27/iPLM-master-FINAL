import dataclasses
from django.contrib.messages.api import error
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from . import filters
from .forms import *
from .models import *
from django.conf import PASSWORD_RESET_TIMEOUT_DAYS_DEPRECATED_MSG, os
from iPLMver2.settings import EMAIL_HOST_USER
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect, Http404, request
from django.contrib import messages
from django.conf import settings
from django.views.generic import View
from django.template.loader import get_template
from django.utils.datastructures import MultiValueDictKeyError
from .utils import render_to_pdf
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.forms import inlineformset_factory
from django.db.models import Avg, Sum
from django.core.mail import EmailMultiAlternatives, send_mail, EmailMessage, BadHeaderError
from CRS.models import FacultyApplicant
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

def error_404_view(request,exception):
    return render(request, 'error.html')

def error_500_view(request):
    return render(request, 'error2.html')

def aboutUs(request):
    return render(request, 'aboutUs.html')

def get_notifications(user_id):
    try :
        return Notification.objects.filter(user_id=user_id)
    except Notification.DoesNotExist:
        return None

def send_notifications(user_id, title, description):
    Notification(user_id=user_id, title=title, description=description)
    Notification.save()
    return 'Successfully Send Notification'
    
def index(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            type_obj = request.user
            if user.is_authenticated and type_obj.is_chairperson:
                return redirect('chairperson')
            elif user.is_authenticated and type_obj.is_admin:
                return redirect('admin')
            elif user.is_authenticated and type_obj.is_faculty:
                return redirect('fHome')
            elif user.is_authenticated and type_obj.is_student:
                return redirect('sHome')
            else:
                messages.error (request,'You have entered an invalid email or password.')
                return render(request, 'index.html')
        
        else:
                messages.error (request,'You have entered an invalid email or password.')
                return render(request, 'index.html')
    return render(request, 'index.html')


# ------------------ CHAIRPERSON VIEWS ------------------------
def choose_one(request):
    type_obj = request.user
    if request.user.is_authenticated and type_obj.is_chairperson and type_obj.is_admin and type_obj.is_faculty:
        return render(request, 'choose_one.html')


def chairperson(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        user = request.user
        acad = AcademicYearInfo.objects.all
        fname = request.user.firstName
        mname = request.user.middleName
        lname = request.user.lastName
        id = request.user.id
        cperson = FacultyInfo.objects.get(pk=id)
        if cperson.departmentID.courseName == "BSIT":
            counts = StudentInfo.objects.filter(studentCourse='BSIT').count()
            countf = FacultyInfo.objects.filter(departmentID=cperson.departmentID).count()
            college = College.objects.filter(collegeName='CET')
            countsub = subjectInfo.objects.filter(college__in=college).count()
        elif cperson.departmentID.courseName == "BSEE":
            counts = StudentInfo.objects.filter(studentCourse='BSEE').count()
            countf = FacultyInfo.objects.filter(departmentID=cperson.departmentID).count()
            college = College.objects.filter(collegeName='CET')
            countsub = subjectInfo.objects.filter(college__in=college).count()
        notifications = get_notifications(id)
        return render(request, './chairperson/chairperson.html', {'user': user, 'fname': fname, 'mname': mname,
                                                                  'lname': lname, 'counts': counts, 'countf': countf,
                                                                  'countsub': countsub, 'acad': acad, 'notifications': notifications})
    else:
        return redirect('index')    

def chairperson_profile(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = FacultyInfo.objects.get(facultyUser=id)
        context = {'id': id, 'info':info, 'acad': acad}
        return render(request, 'chairperson/Home/chairperson_view_profile.html',context)
    else:
        return redirect('index')

def chairperson_edit_profile(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        user = request.user
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        if request.method == 'POST':
            info.facultyContact = request.POST.get('newContact')
            user.save()
            info.save()
            messages.success(request, 'Profile Updated!')
            return redirect('chairperson_profile')
        return render(request, 'chairperson/Home/chairperson_edit_profile.html',
                      { 'info': info, 'user':user})
    else:
        return redirect('index')

def chairperson_change_password(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password Updated!')
                return redirect('chairperson_profile')
            else:
                messages.error(request, 'Your password must contain at least 1 uppercase letter, A-Z.')
                messages.error(request, 'Your password must contain at least 1 lowercase letter, a-z.')
                messages.error(request, 'Your password must contain at least 1 symbol character, /@!.')
                messages.error(request, 'Your password must have 8 minimum characters.')
                messages.error(request, '"Re-typed password must match to the new password"')
        else:
            form = PasswordChangeForm(request.user)
        return render(request, 'chairperson/Home/chairperson_change_password.html', {'form': form})
    else:
        return redirect('index')

# Department (Chairperson)
def is_active(request):
    subject = studentScheduling.objects.all 
    #bsit1 = SubjectSchedule.objects.filter(yearStanding='First Year')
    #bsit2 = SubjectSchedule.objects.filter(yearStanding='Second Year')
    #bsit3 = SubjectSchedule.objects.filter(yearStanding='Third Year')
    #bsit4 = SubjectSchedule.objects.filter(yearStanding='Fourth Year')
    #bsit5 = SubjectSchedule.objects.filter(yearStanding='Fifth Year')
    #bsit6 = SubjectSchedule.objects.filter(yearStanding='Sixth Year')
    context = {'subject' : subject}
    return render(request, './chairperson/Department/is_active.html', context)

def is_subject_view(request, dept_id):
    subj = studentScheduling.objects.get(pk=dept_id)
    students = StudentInfo.objects.filter(studentSection = subj.realsection)
    count = students.count()
    result = filters.Search(request.GET, queryset=students); students = result.qs
    context = {'subj': subj, 'students': students, 'result': result, 'count' : count}
    return render(request, './chairperson/Department/is_subject_view.html', context)

def sc_active(request):
    subject = studentScheduling.objects.all
    return render(request, './chairperson/Department/sc_active.html', {'subject': subject})

def sc_subject_view(request, dept_id):
    subj = studentScheduling.objects.get(pk=dept_id)
    students = StudentInfo.objects.filter(studentSection = subj.realsection)
    count = students.count()
    result = filters.Search(request.GET, queryset=students); students = result.qs
    context = {'subj': subj, 'students': students, 'result': result, 'count' : count}
    return render(request, './chairperson/Department/sc_subject_view.html', context)

# Students (Chairperson)
def dept_student(request):
    id = request.user.id
    cperson = FacultyInfo.objects.get(pk=id)
    if cperson.departmentID.courseName == "BSIT":
        return redirect('students_bsit1')
    elif cperson.departmentID.courseName == "BSEE":
        return redirect('students_bsee1')


def students_all(request):
    bsit = StudentInfo.objects.filter(studentCourse='BSIT'); count = bsit.count()
    result = filters.Search(request.GET, queryset=bsit); bsit = result.qs
    year = "All"
    context = {'bsit': bsit, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_all.html', context)
def students_allI(request):
    bsit = StudentInfo.objects.filter(studentRegStatus='Irregular', studentCourse='BSIT'); count = bsit.count()
    result = filters.Search(request.GET, queryset=bsit); bsit = result.qs
    year = "All"
    context = {'bsit': bsit, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_allI.html', context)


def students_bsit(request):
    bsit1 = StudentInfo.objects.filter(studentYearlevel='1', studentCourse='BSIT'); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = 'First Year'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit.html', context)
def students_bsit1I(request):
    bsit1 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='1', studentCourse='BSIT'); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = 'First Year'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit1I.html', context)


def students_bsit2(request):
    bsit2 = StudentInfo.objects.filter(studentYearlevel='2', studentCourse='BSIT'); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = 'Second Year'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit2.html', context)
def students_bsit2I(request):
    bsit2 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='2', studentCourse='BSIT'); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = 'Second Year'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit2I.html', context)


def students_bsit3(request):
    bsit3 = StudentInfo.objects.filter(studentYearlevel='3', studentCourse='BSIT'); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = 'Third Year'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit3.html', context)
def students_bsit3I(request):
    bsit3 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='3', studentCourse='BSIT'); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = 'Third Year'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit3I.html', context)


def students_bsit4(request):
    bsit4 = StudentInfo.objects.filter(studentYearlevel='4', studentCourse='BSIT'); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = 'Fourth Year'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit4.html', context)
def students_bsit4I(request):
    bsit4 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='4', studentCourse='BSIT'); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = 'Fourth Year'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit4I.html', context)

def students_bsit5(request):
    bsit5 = StudentInfo.objects.filter(studentYearlevel='5', studentCourse='BSIT'); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = 'Fifth Year'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit5.html', context)
def students_bsit5I(request):
    bsit5 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='5', studentCourse='BSIT'); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = 'Fifth Year'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit5I.html', context)


def students_bsit6(request):
    bsit6 = StudentInfo.objects.filter(studentYearlevel='6', studentCourse='BSIT'); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = 'Sixth Year'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit6.html', context)
def students_bsit6I(request):
    bsit6 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='6', studentCourse='BSIT'); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = 'Sixth Year'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students/students_bsit6I.html', context)


def students_allbsee(request):
    bsee = StudentInfo.objects.filter(studentCourse='BSEE'); count = bsee.count()
    result = filters.Search(request.GET, queryset=bsee); bsee = result.qs
    year = "All"
    context = {'bsee': bsee, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_allbsee.html', context)
def students_allIbsee(request):
    bsit = StudentInfo.objects.filter(studentCourse='BSEE', studentRegStatus='Irregular'); count = bsit.count()
    result = filters.Search(request.GET, queryset=bsit); bsit = result.qs
    year = "All"
    context = {'bsit': bsit, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_allIbsee.html', context)

def students_bsee(request):
    bsit1 = StudentInfo.objects.filter(studentYearlevel='1', studentCourse='BSEE'); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = 'First Year'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee.html', context)
def students_bsee1I(request):
    bsit1 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='1', studentCourse='BSEE'); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = 'First Year'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee1I.html', context)

def students_bsee2(request):
    bsit2 = StudentInfo.objects.filter(studentYearlevel='2', studentCourse='BSEE'); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = 'Second Year'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee2.html', context)
def students_bsee2I(request):
    bsit2 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='2', studentCourse='BSEE');  count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = 'Second Year'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee2I.html', context)

def students_bsee3(request):
    bsit3 = StudentInfo.objects.filter(studentYearlevel='3', studentCourse='BSEE'); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = 'Third Year'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee3.html', context)
def students_bsee3I(request):
    bsit3 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='3', studentCourse='BSEE'); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = 'Third Year'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee3I.html', context)

def students_bsee4(request):
    bsit4 = StudentInfo.objects.filter(studentYearlevel='4', studentCourse='BSEE'); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = 'Fourth Year'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee4.html', context)
def students_bsee4I(request):
    bsit4 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='4', studentCourse='BSEE'); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = 'Fourth Year'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee4I.html', context)

def students_bsee5(request):
    bsit5 = StudentInfo.objects.filter(studentYearlevel='5', studentCourse='BSEE'); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = 'Fifth Year'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee5.html', context)
def students_bsee5I(request):
    bsit5 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='5', studentCourse='BSEE'); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = 'Fifth Year'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee5I.html', context)

def students_bsee6(request):
    bsit6 = StudentInfo.objects.filter(studentYearlevel='6', studentCourse='BSEE'); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = 'Sixth Year'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee6.html', context)
def students_bsee6I(request):
    bsit6 = StudentInfo.objects.filter(studentRegStatus='Irregular', studentYearlevel='6', studentCourse='BSEE'); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = 'Sixth Year'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year}
    return render(request, './chairperson/students BSEE/students_bsee6I.html', context)


def profile1_1(request, dept_id):
    p11 = StudentInfo.objects.get(pk=dept_id)
    context = {'p11': p11}
    return render(request, './chairperson/students/profile1_1.html', context)
def profile1_1bsee(request, bsee_id):
    p11 = StudentInfo.objects.get(pk=bsee_id)
    context = {'p11': p11}
    return render(request, './chairperson/students BSEE/profile1_1bsee.html', context)


def students_bsit1(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="1", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '1'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1.html', context)
def students_bsit1_2(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="2", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '2'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1-2.html', context)
def students_bsit1_3(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="3", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '3'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1-3.html', context)
def students_bsit1_4(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="4", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '4'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1-4.html', context)
def students_bsit1_5(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="5", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '5'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1-5.html', context)
def students_bsit1_6(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="6", blockCourse='BSIT')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '6'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1-6.html', context)

def students_bsit2_1(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="1", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '1'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2-1.html', context)
def students_bsit2_2(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="2", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '2'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2-2.html', context)
def students_bsit2_3(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="3", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '3'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1}
    return render(request, './chairperson/students/students_bsit2-3.html', context)
def students_bsit2_4(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="4", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '4'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2-4.html', context)
def students_bsit2_5(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="5", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '5'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2-5.html', context)
def students_bsit2_6(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="6", blockCourse='BSIT')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '6'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2-6.html', context)

def students_bsit3_1(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="1", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '1'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-1.html', context)
def students_bsit3_2(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="2", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '2'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-2.html', context)
def students_bsit3_3(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="3", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '3'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-3.html', context)
def students_bsit3_4(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="4", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '4'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-4.html', context)
def students_bsit3_5(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="5", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '5'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-5.html', context)
def students_bsit3_6(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="6", blockCourse='BSIT')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '6'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3-6.html', context)

def students_bsit4_1(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="1", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '1'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-1.html', context)
def students_bsit4_2(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="2", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '2'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-2.html', context)
def students_bsit4_3(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="3", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '3'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-3.html', context)
def students_bsit4_4(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="4", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '4'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-4.html', context)
def students_bsit4_5(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="5", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '5'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-5.html', context)
def students_bsit4_6(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="6", blockCourse='BSIT')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '6'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4-6.html', context)

def students_bsit5_1(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="1", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '1'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-1.html', context)
def students_bsit5_2(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="2", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '2'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-2.html', context)
def students_bsit5_3(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="3", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '3'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-3.html', context)
def students_bsit5_4(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="4", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '4'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-4.html', context)
def students_bsit5_5(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="5", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '5'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-5.html', context)
def students_bsit5_6(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="6", blockCourse='BSIT')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '6'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5-6.html', context)

def students_bsit6_1(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="1", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '1'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-1.html', context)
def students_bsit6_2(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="2", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '2'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-2.html', context)
def students_bsit6_3(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="3", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '3'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-3.html', context)
def students_bsit6_4(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="4", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '4'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-4.html', context)
def students_bsit6_5(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="5", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '5'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-5.html', context)
def students_bsit6_6(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="6", blockCourse='BSIT')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '6'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6-6.html', context)

def students_bsee1(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="1", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '1'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1.html', context)
def students_bsee1_2(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="2", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '2'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1-2.html', context)
def students_bsee1_3(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="3", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '3'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1-3.html', context)
def students_bsee1_4(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="4", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '4'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1-4.html', context)
def students_bsee1_5(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="5", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '5'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1-5.html', context)
def students_bsee1_6(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="6", blockCourse='BSEE')
    bsit1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1.count()
    result = filters.Search(request.GET, queryset=bsit1); bsit1 = result.qs
    year = '1st Year'; block1 = '6'
    context = {'bsit1': bsit1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1-6.html', context)

def students_bsee2_1(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="1", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '1'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-1.html', context)
def students_bsee2_2(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="2", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '2'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-2.html', context)
def students_bsee2_3(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="3", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '3'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-3.html', context)
def students_bsee2_4(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="4", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '4'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-4.html', context)
def students_bsee2_5(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="5", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '5'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-5.html', context)
def students_bsee2_6(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="6", blockCourse='BSEE')
    bsit2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2.count()
    result = filters.Search(request.GET, queryset=bsit2); bsit2 = result.qs
    year = '2nd Year'; block1 = '6'
    context = {'bsit2': bsit2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2-6.html', context)

def students_bsee3_1(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="1", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '1'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-1.html', context)
def students_bsee3_2(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="2", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '2'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-2.html', context)
def students_bsee3_3(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="3", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '3'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-3.html', context)
def students_bsee3_4(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="4", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '4'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-4.html', context)
def students_bsee3_5(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="5", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '5'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-5.html', context)
def students_bsee3_6(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="6", blockCourse='BSEE')
    bsit3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3.count()
    result = filters.Search(request.GET, queryset=bsit3); bsit3 = result.qs
    year = '3rd Year'; block1 = '6'
    context = {'bsit3': bsit3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3-6.html', context)

def students_bsee4_1(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="1", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '1'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-1.html', context)
def students_bsee4_2(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="2", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '2'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-2.html', context)
def students_bsee4_3(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="3", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '3'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-3.html', context)
def students_bsee4_4(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="4", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '4'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-4.html', context)
def students_bsee4_5(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="5", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '5'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-5.html', context)
def students_bsee4_6(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="6", blockCourse='BSEE')
    bsit4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4.count()
    result = filters.Search(request.GET, queryset=bsit4); bsit4 = result.qs
    year = '4th Year'; block1 = '6'
    context = {'bsit4': bsit4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4-6.html', context)

def students_bsee5_1(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="1", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '1'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-1.html', context)
def students_bsee5_2(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="2", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '2'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-2.html', context)
def students_bsee5_3(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="3", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '3'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-3.html', context)
def students_bsee5_4(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="4", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '4'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-4.html', context)
def students_bsee5_5(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="5", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '5'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-5.html', context)
def students_bsee5_6(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="6", blockCourse='BSEE')
    bsit5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5.count()
    result = filters.Search(request.GET, queryset=bsit5); bsit5 = result.qs
    year = '5th Year'; block1 = '6'
    context = {'bsit5': bsit5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5-6.html', context)

def students_bsee6_1(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="1", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '1'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-1.html', context)
def students_bsee6_2(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="2", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '2'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-2.html', context)
def students_bsee6_3(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="3", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '3'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-3.html', context)
def students_bsee6_4(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="4", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '4'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-4.html', context)
def students_bsee6_5(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="5", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '5'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-5.html', context)
def students_bsee6_6(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="6", blockCourse='BSEE')
    bsit6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6.count()
    result = filters.Search(request.GET, queryset=bsit6); bsit6 = result.qs
    year = '6th Year'; block1 = '6'
    context = {'bsit6': bsit6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6-6.html', context)

def edit_students(request,pk):
    i = get_object_or_404(StudentInfo, pk=pk)

    if request.method == 'POST':
        user_form = StudentsForm(request.POST, instance=i)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            return redirect('students_bsit1')

    else:
        user_form = StudentsForm(instance=i)
    return render(request, './chairperson/students/edit_students.html',
                  {'user_form': user_form})

def edit_studentsbsee(request,pk):
    i = get_object_or_404(StudentInfo, pk=pk)

    if request.method == 'POST':
        user_form = StudentsForm(request.POST, instance=i)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            return redirect('students_bsee1')

    else:
        user_form = StudentsForm(instance=i)
    return render(request, './chairperson/students/edit_students.html',
                  {'user_form': user_form})

def students_bsit1B1(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="1", blockCourse='BSIT')
    bsit1B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B1.count()
    result = filters.Search(request.GET, queryset=bsit1B1); bsit1B1 = result.qs
    year = '1st Year'; block1 = '1'
    context = {'bsit1B1': bsit1B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B1.html', context)
def students_bsit1B2(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="2", blockCourse='BSIT')
    bsit1B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B2.count()
    result = filters.Search(request.GET, queryset=bsit1B2); bsit1B2 = result.qs
    year = '1st Year'; block1 = '2'
    context = {'bsit1B2': bsit1B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B2.html', context)
def students_bsit1B3(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="3", blockCourse='BSIT')
    bsit1B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B3.count()
    result = filters.Search(request.GET, queryset=bsit1B3); bsit1B3 = result.qs
    year = '1st Year'; block1 = '3'
    context = {'bsit1B3': bsit1B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B3.html', context)
def students_bsit1B4(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="4", blockCourse='BSIT')
    bsit1B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B4.count()
    result = filters.Search(request.GET, queryset=bsit1B4); bsit1B4 = result.qs
    year = '1st Year'; block1 = '4'
    context = {'bsit1B4': bsit1B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B4.html', context)
def students_bsit1B5(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="5", blockCourse='BSIT')
    bsit1B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B5.count()
    result = filters.Search(request.GET, queryset=bsit1B5); bsit1B5 = result.qs
    year = '1st Year'; block1 = '5'
    context = {'bsit1B5': bsit1B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B5.html', context)
def students_bsit1B6(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="6", blockCourse='BSIT')
    bsit1B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit1B6.count()
    result = filters.Search(request.GET, queryset=bsit1B6); bsit1B6 = result.qs
    year = '1st Year'; block1 = '6'
    context = {'bsit1B6': bsit1B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit1B6.html', context)

def students_bsit2B1(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="1", blockCourse='BSIT')
    bsit2B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B1.count()
    result = filters.Search(request.GET, queryset=bsit2B1); bsit2B1 = result.qs
    year = '2nd Year'; block1 = '1'
    context = {'bsit2B1': bsit2B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2B1.html', context)
def students_bsit2B2(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="2", blockCourse='BSIT')
    bsit2B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B2.count()
    result = filters.Search(request.GET, queryset=bsit2B2); bsit2B2 = result.qs
    year = '2nd Year'; block1 = '2'
    context = {'bsit2B2': bsit2B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2B2.html', context)
def students_bsit2B3(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="3", blockCourse='BSIT')
    bsit2B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B3.count()
    result = filters.Search(request.GET, queryset=bsit2B3); bsit2B3 = result.qs
    year = '2nd Year'; block1 = '3'
    context = {'bsit2B3': bsit2B3, 'result': result, 'count': count, 'year': year, 'block1': block1}
    return render(request, './chairperson/students/students_bsit2B3.html', context)
def students_bsit2B4(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="4", blockCourse='BSIT')
    bsit2B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B4.count()
    result = filters.Search(request.GET, queryset=bsit2B4); bsit2B4 = result.qs
    year = '2nd Year'; block1 = '4'
    context = {'bsit2B4': bsit2B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2B4.html', context)
def students_bsit2B5(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="5", blockCourse='BSIT')
    bsit2B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B5.count()
    result = filters.Search(request.GET, queryset=bsit2B5); bsit2B5 = result.qs
    year = '2nd Year'; block1 = '5'
    context = {'bsit2B5': bsit2B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2B5.html', context)
def students_bsit2B6(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="6", blockCourse='BSIT')
    bsit2B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit2B6.count()
    result = filters.Search(request.GET, queryset=bsit2B6); bsit2B6 = result.qs
    year = '2nd Year'; block1 = '6'
    context = {'bsit2B6': bsit2B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit2B6.html', context)

def students_bsit3B1(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="1", blockCourse='BSIT')
    bsit3B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B1.count()
    result = filters.Search(request.GET, queryset=bsit3B1); bsit3B1 = result.qs
    year = '3rd Year'; block1 = '1'
    context = {'bsit3B1': bsit3B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B1.html', context)
def students_bsit3B2(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="2", blockCourse='BSIT')
    bsit3B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B2.count()
    result = filters.Search(request.GET, queryset=bsit3B2); bsit3B2 = result.qs
    year = '3rd Year'; block1 = '2'
    context = {'bsit3B2': bsit3B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B2.html', context)
def students_bsit3B3(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="3", blockCourse='BSIT')
    bsit3B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B3.count()
    result = filters.Search(request.GET, queryset=bsit3B3); bsit3B3 = result.qs
    year = '3rd Year'; block1 = '3'
    context = {'bsit3B3': bsit3B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B3.html', context)
def students_bsit3B4(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="4", blockCourse='BSIT')
    bsit3B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B4.count()
    result = filters.Search(request.GET, queryset=bsit3B4); bsit3B4 = result.qs
    year = '3rd Year'; block1 = '4'
    context = {'bsit3B4': bsit3B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B4.html', context)
def students_bsit3B5(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="5", blockCourse='BSIT')
    bsit3B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B5.count()
    result = filters.Search(request.GET, queryset=bsit3B5); bsit3B5 = result.qs
    year = '3rd Year'; block1 = '5'
    context = {'bsit3B5': bsit3B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B5.html', context)
def students_bsit3B6(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="6", blockCourse='BSIT')
    bsit3B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit3B6.count()
    result = filters.Search(request.GET, queryset=bsit3B6); bsit3B6 = result.qs
    year = '3rd Year'; block1 = '6'
    context = {'bsit3B6': bsit3B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit3B6.html', context)

def students_bsit4B1(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="1", blockCourse='BSIT')
    bsit4B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B1.count()
    result = filters.Search(request.GET, queryset=bsit4B1); bsit4B1 = result.qs
    year = '4th Year'; block1 = '1'
    context = {'bsit4B1': bsit4B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B1.html', context)
def students_bsit4B2(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="2", blockCourse='BSIT')
    bsit4B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B2.count()
    result = filters.Search(request.GET, queryset=bsit4B2); bsit4B2 = result.qs
    year = '4th Year'; block1 = '2'
    context = {'bsit4B2': bsit4B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B2.html', context)
def students_bsit4B3(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="3", blockCourse='BSIT')
    bsit4B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B3.count()
    result = filters.Search(request.GET, queryset=bsit4B3); bsit4B3 = result.qs
    year = '4th Year'; block1 = '3'
    context = {'bsit4B3': bsit4B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B3.html', context)
def students_bsit4B4(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="4", blockCourse='BSIT')
    bsit4B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B4.count()
    result = filters.Search(request.GET, queryset=bsit4B4); bsit4B4 = result.qs
    year = '4th Year'; block1 = '4'
    context = {'bsit4B4': bsit4B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B4.html', context)
def students_bsit4B5(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="5", blockCourse='BSIT')
    bsit4B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B5.count()
    result = filters.Search(request.GET, queryset=bsit4B5); bsit4B5 = result.qs
    year = '4th Year'; block1 = '5'
    context = {'bsit4B5': bsit4B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B5.html', context)
def students_bsit4B6(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="6", blockCourse='BSIT')
    bsit4B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit4B6.count()
    result = filters.Search(request.GET, queryset=bsit4B6); bsit4B6 = result.qs
    year = '4th Year'; block1 = '6'
    context = {'bsit4B6': bsit4B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit4B4.html', context)

def students_bsit5B1(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="1", blockCourse='BSIT')
    bsit5B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B1.count()
    result = filters.Search(request.GET, queryset=bsit5B1); bsit5B1 = result.qs
    year = '5th Year'; block1 = '1'
    context = {'bsit5B1': bsit5B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B1.html', context)
def students_bsit5B2(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="2", blockCourse='BSIT')
    bsit5B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B2.count()
    result = filters.Search(request.GET, queryset=bsit5B2); bsit5B2 = result.qs
    year = '5th Year'; block1 = '2'
    context = {'bsit5B2': bsit5B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B2.html', context)
def students_bsit5B3(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="3", blockCourse='BSIT')
    bsit5B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B3.count()
    result = filters.Search(request.GET, queryset=bsit5B3); bsit5B3 = result.qs
    year = '5th Year'; block1 = '3'
    context = {'bsit5B3': bsit5B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B3.html', context)
def students_bsit5B4(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="4", blockCourse='BSIT')
    bsit5B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B4.count()
    result = filters.Search(request.GET, queryset=bsit5B4); bsit5B4 = result.qs
    year = '5th Year'; block1 = '4'
    context = {'bsit5B4': bsit5B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B4.html', context)
def students_bsit5B5(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="5", blockCourse='BSIT')
    bsit5B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B5.count()
    result = filters.Search(request.GET, queryset=bsit5B5); bsit5B5 = result.qs
    year = '5th Year'; block1 = '5'
    context = {'bsit5B5': bsit5B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B5.html', context)
def students_bsit5B6(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="6", blockCourse='BSIT')
    bsit5B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit5B6.count()
    result = filters.Search(request.GET, queryset=bsit5B6); bsit5B6 = result.qs
    year = '5th Year'; block1 = '6'
    context = {'bsit5B6': bsit5B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit5B6.html', context)

def students_bsit6B1(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="1", blockCourse='BSIT')
    bsit6B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B1.count()
    result = filters.Search(request.GET, queryset=bsit6B1); bsit6B1 = result.qs
    year = '6th Year'; block1 = '1'
    context = {'bsit6B1': bsit6B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B1.html', context)
def students_bsit6B2(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="2", blockCourse='BSIT')
    bsit6B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B2.count()
    result = filters.Search(request.GET, queryset=bsit6B2); bsit6B2 = result.qs
    year = '6th Year'; block1 = '2'
    context = {'bsit6B2': bsit6B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B2.html', context)
def students_bsit6B3(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="3", blockCourse='BSIT')
    bsit6B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B3.count()
    result = filters.Search(request.GET, queryset=bsit6B3); bsit6B3 = result.qs
    year = '6th Year'; block1 = '3'
    context = {'bsit6B3': bsit6B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B3.html', context)
def students_bsit6B4(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="4", blockCourse='BSIT')
    bsit6B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B4.count()
    result = filters.Search(request.GET, queryset=bsit6B4); bsit6B4 = result.qs
    year = '6th Year'; block1 = '4'
    context = {'bsit6B4': bsit6B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B4.html', context)
def students_bsit6B5(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="5", blockCourse='BSIT')
    bsit6B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B5.count()
    result = filters.Search(request.GET, queryset=bsit6B5); bsit6B5 = result.qs
    year = '6th Year'; block1 = '5'
    context = {'bsit6B5': bsit6B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B5.html', context)
def students_bsit6B6(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="6", blockCourse='BSIT')
    bsit6B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsit6B6.count()
    result = filters.Search(request.GET, queryset=bsit6B6); bsit6B6 = result.qs
    year = '6th Year'; block1 = '6'
    context = {'bsit6B6': bsit6B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students/students_bsit6B6.html', context)

def students_bsee1B1(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="1", blockCourse='BSEE')
    bsee1B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B1.count()
    result = filters.Search(request.GET, queryset=bsee1B1); bsee1B1 = result.qs
    year = '1st Year'; block1 = '1'
    context = {'bsee1B1': bsee1B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B1.html', context)
def students_bsee1B2(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="2", blockCourse='BSEE')
    bsee1B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B2.count()
    result = filters.Search(request.GET, queryset=bsee1B2); bsee1B2 = result.qs
    year = '1st Year'; block1 = '2'
    context = {'bsee1B2': bsee1B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B2.html', context)
def students_bsee1B3(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="3", blockCourse='BSEE')
    bsee1B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B3.count()
    result = filters.Search(request.GET, queryset=bsee1B3); bsee1B3 = result.qs
    year = '1st Year'; block1 = '3'
    context = {'bsee1B3': bsee1B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B3.html', context)
def students_bsee1B4(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="4", blockCourse='BSEE')
    bsee1B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B4.count()
    result = filters.Search(request.GET, queryset=bsee1B4); bsee1B4 = result.qs
    year = '1st Year'; block1 = '4'
    context = {'bsee1B4': bsee1B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B4.html', context)
def students_bsee1B5(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="5", blockCourse='BSEE')
    bsee1B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B5.count()
    result = filters.Search(request.GET, queryset=bsee1B5); bsee1B5 = result.qs
    year = '1st Year'; block1 = '5'
    context = {'bsee1B5': bsee1B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B5.html', context)
def students_bsee1B6(request):
    section = BlockSection.objects.filter(blockYear="1", blockSection="6", blockCourse='BSEE')
    bsee1B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee1B6.count()
    result = filters.Search(request.GET, queryset=bsee1B6); bsee1B6 = result.qs
    year = '1st Year'; block1 = '6'
    context = {'bsee1B6': bsee1B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee1B6.html', context)

def students_bsee2B1(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="1", blockCourse='BSEE')
    bsee2B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B1.count()
    result = filters.Search(request.GET, queryset=bsee2B1); bsee2B1 = result.qs
    year = '2nd Year'; block1 = '1'
    context = {'bsee2B1': bsee2B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B1.html', context)
def students_bsee2B2(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="2", blockCourse='BSEE')
    bsee2B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B2.count()
    result = filters.Search(request.GET, queryset=bsee2B2); bsee2B2 = result.qs
    year = '2nd Year'; block1 = '2'
    context = {'bsee2B2': bsee2B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B2.html', context)
def students_bsee2B3(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="3", blockCourse='BSEE')
    bsee2B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B3.count()
    result = filters.Search(request.GET, queryset=bsee2B3); bsee2B3 = result.qs
    year = '2nd Year'; block1 = '3'
    context = {'bsee2B3': bsee2B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B3.html', context)
def students_bsee2B4(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="4", blockCourse='BSEE')
    bsee2B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B4.count()
    result = filters.Search(request.GET, queryset=bsee2B4); bsee2B4 = result.qs
    year = '2nd Year'; block1 = '4'
    context = {'bsee2B4': bsee2B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B4.html', context)
def students_bsee2B5(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="5", blockCourse='BSEE')
    bsee2B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B5.count()
    result = filters.Search(request.GET, queryset=bsee2B5); bsee2B5 = result.qs
    year = '2nd Year'; block1 = '5'
    context = {'bsee2B5': bsee2B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B5.html', context)
def students_bsee2B6(request):
    section = BlockSection.objects.filter(blockYear="2", blockSection="6", blockCourse='BSEE')
    bsee2B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee2B6.count()
    result = filters.Search(request.GET, queryset=bsee2B6); bsee2B6 = result.qs
    year = '2nd Year'; block1 = '6'
    context = {'bsee2B6': bsee2B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee2B6.html', context)

def students_bsee3B1(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="1", blockCourse='BSEE')
    bsee3B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B1.count()
    result = filters.Search(request.GET, queryset=bsee3B1); bsee3B1 = result.qs
    year = '3rd Year'; block1 = '1'
    context = {'bsee3B1': bsee3B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B1.html', context)
def students_bsee3B2(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="2", blockCourse='BSEE')
    bsee3B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B2.count()
    result = filters.Search(request.GET, queryset=bsee3B2); bsee3B2 = result.qs
    year = '3rd Year'; block1 = '2'
    context = {'bsee3B2': bsee3B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B2.html', context)
def students_bsee3B3(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="3", blockCourse='BSEE')
    bsee3B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B3.count()
    result = filters.Search(request.GET, queryset=bsee3B3); bsee3B3 = result.qs
    year = '3rd Year'; block1 = '3'
    context = {'bsee3B3': bsee3B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B3.html', context)
def students_bsee3B4(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="4", blockCourse='BSEE')
    bsee3B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B4.count()
    result = filters.Search(request.GET, queryset=bsee3B4); bsee3B4 = result.qs
    year = '3rd Year'; block1 = '4'
    context = {'bsee3B4': bsee3B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B4.html', context)
def students_bsee3B5(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="5", blockCourse='BSEE')
    bsee3B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B5.count()
    result = filters.Search(request.GET, queryset=bsee3B5); bsee3B5 = result.qs
    year = '3rd Year'; block1 = '5'
    context = {'bsee3B5': bsee3B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B5.html', context)
def students_bsee3B6(request):
    section = BlockSection.objects.filter(blockYear="3", blockSection="6", blockCourse='BSEE')
    bsee3B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee3B6.count()
    result = filters.Search(request.GET, queryset=bsee3B6); bsee3B6 = result.qs
    year = '3rd Year'; block1 = '6'
    context = {'bsee3B6': bsee3B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee3B6.html', context)

def students_bsee4B1(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="1", blockCourse='BSEE')
    bsee4B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B1.count()
    result = filters.Search(request.GET, queryset=bsee4B1); bsee4B1 = result.qs
    year = '4th Year'; block1 = '1'
    context = {'bsee4B1': bsee4B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B1.html', context)
def students_bsee4B2(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="2", blockCourse='BSEE')
    bsee4B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B2.count()
    result = filters.Search(request.GET, queryset=bsee4B2); bsee4B2 = result.qs
    year = '4th Year'; block1 = '2'
    context = {'bsee4B2': bsee4B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B2.html', context)
def students_bsee4B3(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="3", blockCourse='BSEE')
    bsee4B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B3.count()
    result = filters.Search(request.GET, queryset=bsee4B3); bsee4B3 = result.qs
    year = '4th Year'; block1 = '3'
    context = {'bsee4B3': bsee4B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B3.html', context)
def students_bsee4B4(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="4", blockCourse='BSEE')
    bsee4B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B4.count()
    result = filters.Search(request.GET, queryset=bsee4B4); bsee4B4 = result.qs
    year = '4th Year'; block1 = '4'
    context = {'bsee4B4': bsee4B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B4.html', context)
def students_bsee4B5(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="5", blockCourse='BSEE')
    bsee4B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B5.count()
    result = filters.Search(request.GET, queryset=bsee4B5); bsee4B5 = result.qs
    year = '4th Year'; block1 = '5'
    context = {'bsee4B5': bsee4B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B5.html', context)
def students_bsee4B6(request):
    section = BlockSection.objects.filter(blockYear="4", blockSection="6", blockCourse='BSEE')
    bsee4B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee4B6.count()
    result = filters.Search(request.GET, queryset=bsee4B6); bsee4B6 = result.qs
    year = '4th Year'; block1 = '6'
    context = {'bsee4B6': bsee4B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee4B6.html', context)

def students_bsee5B1(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="1", blockCourse='BSEE')
    bsee5B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B1.count()
    result = filters.Search(request.GET, queryset=bsee5B1); bsee5B1 = result.qs
    year = '5th Year'; block1 = '1'
    context = {'bsee5B1': bsee5B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B1.html', context)
def students_bsee5B2(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="2", blockCourse='BSEE')
    bsee5B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B2.count()
    result = filters.Search(request.GET, queryset=bsee5B2); bsee5B2 = result.qs
    year = '5th Year'; block1 = '2'
    context = {'bsee5B2': bsee5B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B2.html', context)
def students_bsee5B3(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="3", blockCourse='BSEE')
    bsee5B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B3.count()
    result = filters.Search(request.GET, queryset=bsee5B3); bsee5B3 = result.qs
    year = '5th Year'; block1 = '3'
    context = {'bsee5B3': bsee5B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B3.html', context)
def students_bsee5B4(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="4", blockCourse='BSEE')
    bsee5B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B4.count()
    result = filters.Search(request.GET, queryset=bsee5B4); bsee5B4 = result.qs
    year = '5th Year'; block1 = '4'
    context = {'bsee5B4': bsee5B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B4.html', context)
def students_bsee5B5(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="5", blockCourse='BSEE')
    bsee5B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B5.count()
    result = filters.Search(request.GET, queryset=bsee5B5); bsee5B5 = result.qs
    year = '5th Year'; block1 = '5'
    context = {'bsee5B5': bsee5B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B5.html', context)
def students_bsee5B6(request):
    section = BlockSection.objects.filter(blockYear="5", blockSection="6", blockCourse='BSEE')
    bsee5B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee5B6.count()
    result = filters.Search(request.GET, queryset=bsee5B6); bsee5B6 = result.qs
    year = '5th Year'; block1 = '6'
    context = {'bsee5B6': bsee5B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee5B6.html', context)

def students_bsee6B1(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="1", blockCourse='BSEE')
    bsee6B1 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B1.count()
    result = filters.Search(request.GET, queryset=bsee6B1); bsee6B1 = result.qs
    year = '6th Year'; block1 = '1'
    context = {'bsee6B1': bsee6B1, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B1.html', context)
def students_bsee6B2(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="2", blockCourse='BSEE')
    bsee6B2 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B2.count()
    result = filters.Search(request.GET, queryset=bsee6B2); bsee6B2 = result.qs
    year = '6th Year'; block1 = '2'
    context = {'bsee6B2': bsee6B2, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B2.html', context)
def students_bsee6B3(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="3", blockCourse='BSEE')
    bsee6B3 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B3.count()
    result = filters.Search(request.GET, queryset=bsee6B3); bsee6B3 = result.qs
    year = '6th Year'; block1 = '3'
    context = {'bsee6B3': bsee6B3, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B3.html', context)
def students_bsee6B4(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="4", blockCourse='BSEE')
    bsee6B4 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B4.count()
    result = filters.Search(request.GET, queryset=bsee6B4); bsee6B4 = result.qs
    year = '6th Year'; block1 = '4'
    context = {'bsee6B4': bsee6B4, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B4.html', context)
def students_bsee6B5(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="5", blockCourse='BSEE')
    bsee6B5 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B5.count()
    result = filters.Search(request.GET, queryset=bsee6B5); bsee6B5 = result.qs
    year = '6th Year'; block1 = '5'
    context = {'bsee6B5': bsee6B5, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B5.html', context)
def students_bsee6B6(request):
    section = BlockSection.objects.filter(blockYear="6", blockSection="6", blockCourse='BSEE')
    bsee6B6 = StudentInfo.objects.filter(studentSection__in=section); count = bsee6B6.count()
    result = filters.Search(request.GET, queryset=bsee6B6); bsee6B6 = result.qs
    year = '6th Year'; block1 = '6'
    context = {'bsee6B6': bsee6B6, 'result': result, 'count': count, 'year': year, 'block1': block1, 'section': section}
    return render(request, './chairperson/students BSEE/students_bsee6B6.html', context)

# Faculty (chairperson)
#def full_time(request):
   # id = request.user.id; cperson = FacultyInfo.objects.get(pdk=id)
    #work_status = FacultyInfo.objects.filter(facultyWorkstatus='Full-Time').filter(departmentID=cperson.departmentID)
    #count = work_status.count()
    #result = filters.Faculty(request.GET, queryset=work_status); work_status = result.qs
    #context = {'work_status': work_status, 'count': count, 'result': result}
    #return render(request, './chairperson/Faculty/full_time.html', context)


def full_time(request):
    id = request.user.id; cperson = FacultyInfo.objects.get(pk=id)
    work_status = FacultyInfo.objects.filter(facultyWorkstatus='Full-Time').filter(departmentID=cperson.departmentID)
    count = work_status.count()
    if request.GET.get('search'):
        search = request.GET['search']
        work_status = FacultyInfo.objects.filter(
            Q(facultyID__contains=search) |
            Q(facultyUser__firstName__icontains=search) |
            Q(facultyUser__lastName__icontains=search) |
            Q(facultyUser__middleName__icontains=search)
        )
    context = {'work_status': work_status, 'count': count}
    return render(request, './chairperson/Faculty/full_time.html', context)

def part_time(request):
    id = request.user.id; cperson = FacultyInfo.objects.get(pk=id)
    work_status = FacultyInfo.objects.filter(facultyWorkstatus='Part-Time').filter(departmentID=cperson.departmentID)
    count = work_status.count()
    result = filters.Faculty(request.GET, queryset=work_status); work_status = result.qs
    context = {'work_status': work_status, 'count': count, 'result': result, }
    return render(request, './chairperson/Faculty/part_time.html', context)

def faculty_schedule(request, dept_id):
    info = FacultyInfo.objects.get(pk=dept_id)
    schedule = studentScheduling.objects.filter(instructor_id=dept_id)
    return render(request, './chairperson/Faculty/faculty_schedule.html', {'info': info, 'schedule' : schedule})

def chairperson_faculty_schedule_edit(request, id):
    if request.user.is_authenticated and request.user.is_chairperson:
        """
        if(request.method == 'GET'):
            asd = studentScheduling.objects.all()
            q = request.GET.get('q')
            if q:
                asd = studentScheduling.objects.filter(
                    Q()
                )
        else:
        """
        c_id=request.user.id
        cperson=FacultyInfo.objects.get(pk=c_id)
        info = FacultyInfo.objects.get(pk=id)
        facultySchedule = studentScheduling.objects.filter(instructor_id=id)
        schedule = studentScheduling.objects.filter(instructor_id=None)
        faculty = studentScheduling.objects.filter(instructor_id=id)
        sum = 0
        for units in faculty:
            n = int(units.subjectCode.subjectUnits)
            sum = sum + n

        return render(request,'./chairperson/Faculty/faculty_editSched.html',{'schedule':schedule,'facultySchedule':facultySchedule,'info' : info,'cperson':cperson,'sum': sum})
    else:
        return redirect ('index')

def remove_faculty_schedule(request,sid,id):
    if request.user.is_authenticated and request.user.is_chairperson:
        fact = studentScheduling.objects.get(id=sid)
        fact.instructor_id = None
        fact.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect ('index')

def add_faculty_schedule(request, sid, id):
    if request.user.is_authenticated and request.user.is_chairperson:
        fact = studentScheduling.objects.get(id=sid)
        fact.instructor_id = id
        facultySchedule = studentScheduling.objects.filter(instructor_id=id)
        validSched = False
        validProf = False
        
        
        subjectIN = str(fact.timeStart)
        sIN = subjectIN.split(":")
        inTimeSubj = float(sIN[0])+float(float(sIN[1])/60)
        subjectOUT = str(fact.timeEnd)
        sOUT = subjectOUT.split(":")
        outTimeSubj = float(sOUT[0])+float(float(sOUT[1])/60)

        profInfo = FacultyInfo.objects.get(facultyUser = id)  
        profAvailIn = str(profInfo.facultyIn).split(':')
        profAvailOut = str(profInfo.facultyOut).split(':')
        FacAvailTimeIn = float(profAvailIn[0])+float(float(profAvailIn[1])/60)
        FacAvailTimeOut = float(profAvailOut[0])+float(float(profAvailOut[1])/60)

        print("IN Get:",inTimeSubj,"Avail:", FacAvailTimeIn)
        print("Out Get:",outTimeSubj,"Avail:", FacAvailTimeOut)
        
        if float(inTimeSubj) < float(FacAvailTimeIn):
            #Input Start Time To Early too Availability
            validProf = False
            errorMessage = "Faculty Time In: " + profAvailIn[0] +":" + profAvailIn[1]+", too early"
        elif float(outTimeSubj) > float(FacAvailTimeOut):
            validProf = False
            errorMessage = "Faculty Time Out" + profAvailOut[0] +":" + profAvailOut[1]+ ", too late"
        else:
            validProf = True
            
        for data in facultySchedule:
            dbSubject = data.subjectCode
            dbSection = data.section
            TimeIn = data.timeStart
            TimeOut = data.timeEnd
            dbDay = data.day
            ListTimeIn = str(TimeIn).split(":")
            ListTimeOut = str(TimeOut).split(":")
            dbTimeIn = float(ListTimeIn[0])+(float(ListTimeIn[1])/60)
            dbTimeOut = float(ListTimeOut[0])+(float(ListTimeOut[1])/60)
            AssignedDay = fact.day
            AssignedTimeInList = str(fact.timeStart).split(":")
            AssignedTimeIn = float(AssignedTimeInList[0])+(float(AssignedTimeInList[1])/60)
            AssignedTimeOutList = str(fact.timeEnd).split(":")
            AssignedTimeOut = float(AssignedTimeOutList[0])+(float(AssignedTimeOutList[1])/60)
            
            if dbDay == AssignedDay:
                if AssignedTimeIn == dbTimeIn:
                    #Same Sched was assigned
                    validSched = False
                    errorMessage = "Schedule Already Exist"
                    break
                if AssignedTimeIn >= dbTimeOut: #Meaning Sched is Later than in the database
                    validSched = True
                else:
                    #Assigned time in is earlier than dbTimeOut
                    if AssignedTimeOut <= dbTimeIn: #Sched is Earlier than test Schedule
                        validSched = True
                    else:
                        #Sched has overlap with Assignedtimeout and dbTimeIn
                        validSched = False
                        errorMessage = "Schedule Overlap at " + str(dbSubject)
                        break
            else:
                validSched = True
        else:
            if facultySchedule.count() == 0 and validProf == True:
                fact.save()
                validSched = False
                validProf = False
                messages.success(request, "Schedule successfully Added!")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if validSched == True and validProf == True:
            fact.save()
            validSched = False
            validProf = False
            messages.success(request, "Schedule successfully Added!")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'Faculty Time Error: %s' % errorMessage)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))        
    else:
        return redirect ('index')


def others_studyplan(request):
    return render(request, './chairperson/Others/cOthers-studyPlan.html')

# -------------------- FACULTY VIEWS ----------------------------------
def fHome(request):
    if request.user.is_authenticated and request.user.is_faculty:
        user = request.user
        facultyInfo = request.user.facultyinfo
        acad = AcademicYearInfo.objects.all
        departmentid=facultyInfo.departmentID_id
        collegeid=facultyInfo.collegeID_id
        college=College.objects.get(id=collegeid)
        department=Department.objects.get(id = departmentid)
        
        return render(request,'./faculty/fHome.html',{'user':user,'facultyInfo':facultyInfo,'department':department,'college':college,'acad':acad})
    else:
        return redirect('index')

def fProfile(request):
    if request.user.is_authenticated and request.user.is_faculty:
        user = request.user
        facultyInfo = request.user.facultyinfo
        departmentid=facultyInfo.departmentID_id
        collegeid=facultyInfo.departmentID_id
        college=College.objects.get(id=collegeid)
        department=Department.objects.get(id = departmentid)
        return render(request,'./faculty/fProfile.html',{'user':user,'facultyInfo':facultyInfo,'department':department,'college':college})
    else:
        return redirect('index')


def fHomeNotification(request):
    return render(request,'./faculty/fHomeNotifications.html')

def fProfileEdit(request):
    if request.user.is_authenticated and request.user.is_faculty:
        user = request.user
        facultyInfo = request.user.facultyinfo
        departmentid=facultyInfo.departmentID_id
        collegeid=facultyInfo.departmentID_id
        college=College.objects.get(id=collegeid)
        department=Department.objects.get(id = departmentid)
        
        if (request.method =='POST'):
            facultyInfo.facultyContact=request.POST.get('newContact')
            user.save()
            facultyInfo.save()
            messages.success(request, 'Profile Updated!')
            return redirect('fProfile')
        return render(request,'./faculty/fProfileEdit.html',{'user':user,'facultyInfo':facultyInfo,'department':department,'college':college})
    else:
        return redirect('index')

def fProfileChangePass(request):
    if request.user.is_authenticated and request.user.is_faculty:
        if (request.method=='POST'):
            form = PasswordChangeForm(request.user,request.POST)
            if form.is_valid():
                user=form.save()
                update_session_auth_hash(request, user)
                messages.success(request,'Password Updated')
                return redirect('fProfile')
            else:
                messages.error(request, 'Your password must contain at least 1 uppercase letter, A-Z.')
                messages.error(request, 'Your password must contain at least 1 lowercase letter, a-z.')
                messages.error(request, 'Your password contain atleast 1 symbol character')
                messages.error(request, 'Your password must have 8 minimum Characters')
                messages.error(request, '"Re-typed password must match to the new password"')
        else:
            form = PasswordChangeForm(request.user)
        return render(request,'./faculty/fProfileChangePass.html',{'form':form})
    else:
         return redirect('index')

def parttime_sched(request):
    if request.user.is_authenticated and request.user.is_faculty:
        user = request.user.id
        f_user = FacultyInfo.objects.get(facultyUser = user)

        if f_user.facultyWorkstatus == 'Part-Time':
            if (request.method=='POST'):
                facultyin = request.POST.get('in')
                facultyout = request.POST.get('out')

                convertIn1 = facultyin.split(":")
                convertIn2 = convertIn1[1].split(" ")
                if convertIn2[1] == 'PM' and int(convertIn1[0]) != 12:
                    newTimeIn = int(convertIn1[0])+12
                else:
                    newTimeIn = int(convertIn1[0])
                TIMEINCONVERT = str(newTimeIn) + ":" + convertIn2[0]

                convertOut1 = facultyout.split(":")
                convertOut2 = convertOut1[1].split(" ")
                if convertOut2[1] == 'PM' and int(convertOut1[0]) != 12:
                    newTimeOut = int(convertOut1[0])+12
                else:
                    newTimeOut = int(convertOut1[0])
                TIMEOUTCONVERT = str(newTimeOut) + ":" + convertOut2[0]

                print("Military Time Conversion:",TIMEINCONVERT,"-",TIMEOUTCONVERT)

                f_in = 0
                outside = 0
                # WAG NA KAYO MAGALIT SA MAHABANG CODE HAHAHAHAHAHAHAHHAHAHAHAHA
                #--- Time in ---
                if TIMEINCONVERT == '7:00':
                    f_in = 0
                if TIMEINCONVERT == '7:30':
                    f_in = 30
                if TIMEINCONVERT == '8:00':
                    f_in = 60
                if TIMEINCONVERT == '8:30':
                    f_in = 90
                if TIMEINCONVERT == '9:00':
                    f_in = 120
                if TIMEINCONVERT == '9:30':
                    f_in = 150
                if TIMEINCONVERT == '10:00':
                    f_in = 180
                if TIMEINCONVERT == '10:30':
                    f_in = 210
                if TIMEINCONVERT == '11:00':
                    f_in = 240
                if TIMEINCONVERT == '11:30':
                    f_in = 270 
                if TIMEINCONVERT == '12:00':
                    f_in = 300
                if TIMEINCONVERT == '12:30':
                    f_in = 330
                if TIMEINCONVERT == '13:00':
                    f_in = 360
                if TIMEINCONVERT == '13:30':
                    f_in = 390
                if TIMEINCONVERT == '14:00':
                    f_in = 410
                if TIMEINCONVERT == '14:30':
                    f_in = 440
                if TIMEINCONVERT == '15:00':
                    f_in = 470
                if TIMEINCONVERT == '15:30':
                    f_in = 500
                if TIMEINCONVERT == '16:00':
                    f_in = 530
                if TIMEINCONVERT == '16:30':
                    f_in = 560
                if TIMEINCONVERT == '17:00':
                    f_in = 590
                if TIMEINCONVERT == '17:30':
                    f_in = 610
                if TIMEINCONVERT == '18:00':
                    f_in = 640
                if TIMEINCONVERT == '18:30':
                    f_in = 670
                if TIMEINCONVERT == '19:00':
                    f_in = 690
                if TIMEINCONVERT == '19:30':
                    f_in = 720
                if TIMEINCONVERT == '20:00':
                    f_in = 750
                
                #--- Time Out ----
                if TIMEOUTCONVERT == '12:00':
                    outside = 300
                if TIMEOUTCONVERT == '12:30':
                    outside = 330
                if TIMEOUTCONVERT == '13:00':
                    outside = 360
                if TIMEOUTCONVERT == '13:30':
                    outside = 390
                if TIMEOUTCONVERT == '14:00':
                    outside = 410
                if TIMEOUTCONVERT == '14:30':
                    outside = 440
                if TIMEOUTCONVERT == '15:00':
                    outside = 470
                if TIMEOUTCONVERT == '15:30':
                    outside = 500
                if TIMEOUTCONVERT == '16:00':
                    outside = 530
                if TIMEOUTCONVERT == '16:30':
                    outside = 560
                if TIMEOUTCONVERT == '17:00':
                    outside = 590
                if TIMEOUTCONVERT == '17:30':
                    outside = 610
                if TIMEOUTCONVERT == '18:00':
                    outside = 640
                if TIMEOUTCONVERT == '18:30':
                    outside = 670
                if TIMEOUTCONVERT == '19:00':
                    outside = 690
                if TIMEOUTCONVERT == '19:30':
                    outside = 720
                if TIMEOUTCONVERT == '20:00':
                    outside = 750
                if TIMEOUTCONVERT == '20:30':
                    outside = 780
                if TIMEOUTCONVERT == '21:00':
                    outside = 810
                if TIMEOUTCONVERT == '21:30':
                    outside = 840
                if TIMEOUTCONVERT == '22:00':
                    outside = 870

                total_teaching_minutes = outside - f_in

                if total_teaching_minutes >= 90 and total_teaching_minutes <= 360:
                    facultyIn=request.POST.get('in')
                    facultyOut=request.POST.get('out')

                    f_user.facultyIn = TIMEINCONVERT
                    f_user.facultyOut = TIMEOUTCONVERT

                    f_user.save()
                    messages.success(request, 'Successfully added your input!')
                    return redirect('parttime_sched')

                else:
                    if total_teaching_minutes < 90:
                        messages.error (request,'Time is below minimum hours!')
                    else:
                        messages.error (request,'Time is above minimum hours!')
        else:
            messages.error (request,'You are not eligible to interact with this page.') 
        return render(request,'./faculty/parttime_sched.html',{'user':user})
    else:
        return redirect('index')


"""def fStudents_advisory(request):
    if request.user.is_authenticated and request.user.is_faculty:
        id= request.user.id
        f_user = FacultyInfo.objects.get(pk = id)
        advisory = BlockSection.objects.filter(adviser = f_user)
        stud_advisory = StudentInfo.objects.filter(studentSection__in = advisory) 
        count = stud_advisory.count()
        if count == 0:
            messages.error (request, 'You have no advisory class!')
            return render (request, './faculty/fStudents_advisory.html')
        context = {'advisory': advisory, 'count': count, 'stud_advisory': stud_advisory}
        return render(request, 'faculty/fStudents_advisory.html', context)
    else:
        return redirect('index')"""

def fStudents_advisory(request):
    if request.user.is_authenticated and request.user.is_faculty:
        id= request.user.id
        f_user = FacultyInfo.objects.get(pk = id)
        advisory = BlockSection.objects.filter(adviser = f_user)
        section = BlockSection.objects.filter(blockYear="1", blockSection="1", blockCourse='BSIT')
        stud_advisory = StudentInfo.objects.filter(studentSection__in = advisory).filter(studentSection__in=section); 
        count = stud_advisory.count()
        if count == 0:
            messages.error (request, 'You have no advisory class!')
            return render (request, './faculty/fStudents_advisory.html')
        context = {'advisory': advisory, 'count': count, 'stud_advisory': stud_advisory}
        return render(request, 'faculty/fStudents_advisory.html', context)
    else:
        return redirect('index')


def fStudents_viewStudentGrade (request,stud_id):
    fcount = 0
    if request.user.is_authenticated and request.user.is_faculty: 
        try:
            checklist = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='1').filter(semTaken='1')
            checklist2 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='1').filter(semTaken='2')
            checklist3 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='2').filter(semTaken='1')
            checklist4 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='2').filter(semTaken='2')
            checklist5 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='3').filter(semTaken='1')
            checklist6 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='3').filter(semTaken='2')
            checklist7 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='4').filter(semTaken='1')
            checklist8 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='4').filter(semTaken='2')
            checklist9 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='5').filter(semTaken='1')
            checklist10 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='5').filter(semTaken='2')
            checklist11 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='6').filter(semTaken='1')
            checklist12 = currchecklist.objects.filter(owner_id=stud_id).filter(yearTaken='6').filter(semTaken='2')
            count = curriculumInfo.objects.filter(counted_in_GWA=True)
            prevunitsum = 0
            prevunitsum2 = 0
            prevunitsum3 = 0
            prevunitsum4 = 0
            prevunitsum5 = 0
            prevunitsum6 = 0
            prevunitsum7 = 0
            prevunitsum8 = 0
            prevunitsum9 = 0
            prevunitsum10 = 0
            prevunitsum11 = 0
            prevunitsum12 = 0
            unitsum = 0 
            unitsum2 = 0
            unitsum3 = 0
            unitsum4 = 0
            unitsum5 = 0
            unitsum6 = 0
            unitsum7 = 0
            unitsum8 = 0
            unitsum9 = 0
            unitsum10 = 0
            unitsum11 = 0
            unitsum12 = 0
            for subj in checklist.filter(curriculumCode__in = count):
                n = float(subj.curriculumCode.subjectUnits)
                g = float(subj.subjectGrades)
                unitprod = n * g
                prevunitsum = prevunitsum+unitprod
                unitsum = unitsum + n
            if prevunitsum == 0:
                ave = 0
            else:
                ave = float(prevunitsum / unitsum)
            for subj in checklist2.filter(curriculumCode__in = count):
                n2 = float(subj.curriculumCode.subjectUnits)
                g2 = float(subj.subjectGrades)
                unitprod2 = n2 * g2
                prevunitsum2 = prevunitsum2+unitprod2
                unitsum2 = unitsum2 + n2
            if prevunitsum2 == 0:
                ave2 = 0
            else:
                ave2 = float(prevunitsum2 / unitsum2)
            for subj in checklist3.filter(curriculumCode__in = count):
                n3 = float(subj.curriculumCode.subjectUnits)
                g3 = float(subj.subjectGrades)
                unitprod3 = n3 * g3
                prevunitsum3 = prevunitsum3+unitprod3
                unitsum3 = unitsum3 + n3
            if prevunitsum3 == 0:
                ave3 = 0
            else:
                ave3 = float(prevunitsum3 / unitsum3)
            for subj in checklist4.filter(curriculumCode__in = count):
                n4 = float(subj.curriculumCode.subjectUnits)
                g4 = float(subj.subjectGrades)
                unitprod4 = n4 * g4
                prevunitsum4 = prevunitsum4+unitprod4
                unitsum4 = unitsum4 + n4
            if prevunitsum4 == 0:
                ave4 = 0
            else:
                ave4 = float(prevunitsum4 / unitsum4)
            for subj in checklist5.filter(curriculumCode__in = count):
                n5 = float(subj.curriculumCode.subjectUnits)
                g5 = float(subj.subjectGrades)
                unitprod5 = n5 * g5
                prevunitsum5 = prevunitsum5+unitprod5
                unitsum5 = unitsum5 + n5
            if prevunitsum5 == 0:
                ave5 = 0
            else:
                ave5 = float(prevunitsum5 / unitsum5)
            for subj in checklist6.filter(curriculumCode__in = count):
                n6 = float(subj.curriculumCode.subjectUnits)
                g6 = float(subj.subjectGrades)
                unitprod6 = n6 * g6
                prevunitsum6 = prevunitsum6+unitprod6
                unitsum6 = unitsum6 + n6
            if prevunitsum6 == 0:
                ave6 = 0
            else:
                ave6 = float(prevunitsum6 / unitsum6)
            for subj in checklist7.filter(curriculumCode__in = count):
                n7 = float(subj.curriculumCode.subjectUnits)
                g7 = float(subj.subjectGrades)
                unitprod7 = n7 * g7
                prevunitsum7 = prevunitsum7+unitprod7
                unitsum7 = unitsum7 + n7
            if prevunitsum7 == 0:
                ave7 = 0
            else:
                ave7 = float(prevunitsum7 / unitsum7)
            for subj in checklist8.filter(curriculumCode__in = count):
                n8 = float(subj.curriculumCode.subjectUnits)
                g8 = float(subj.subjectGrades)
                unitprod8 = n8 * g8
                prevunitsum8 = prevunitsum8+unitprod8
                unitsum8 = unitsum8 + n8
            if prevunitsum8 == 0:
                ave8 = 0
            else:
                ave8 = float(prevunitsum8 / unitsum8)
            for subj in checklist9.filter(curriculumCode__in = count):
                n9 = float(subj.curriculumCode.subjectUnits)
                g9 = float(subj.subjectGrades)
                unitprod9 = n9 * g9
                prevunitsum9 = prevunitsum9+unitprod9
                unitsum9 = unitsum9 + n9
            if prevunitsum9 == 0:
                ave9 = 0
            else:
                ave9 = float(prevunitsum9 / unitsum9)
            for subj in checklist10.filter(curriculumCode__in = count):
                n10 = float(subj.curriculumCode.subjectUnits)
                g10 = float(subj.subjectGrades)
                unitprod10 = n10 * g10
                prevunitsum10 = prevunitsum10+unitprod10
                unitsum10 = unitsum10 + n10
            if prevunitsum10 == 0:
                ave10 = 0
            else:
                ave10 = float(prevunitsum10 / unitsum10)
            for subj in checklist11.filter(curriculumCode__in = count):
                n11 = float(subj.curriculumCode.subjectUnits)
                g11 = float(subj.subjectGrades)
                unitprod11 = n11 * g11
                prevunitsum11 = prevunitsum11+unitprod11
                unitsum11 = unitsum11 + n11
            if prevunitsum11 == 0:
                ave11 = 0
            else:
                ave11 = float(prevunitsum11 / unitsum11)
            for subj in checklist12.filter(curriculumCode__in = count):
                n12 = float(subj.curriculumCode.subjectUnits)
                g12 = float(subj.subjectGrades)
                unitprod12 = n12 * g12
                prevunitsum12 = prevunitsum12+unitprod12
                unitsum12 = unitsum12 + n12
            if prevunitsum12 == 0:
                ave12 = 0
            else:
                ave12 = float(prevunitsum12 / unitsum12)
        except currchecklist.DoesNotExist:
            checklist = None
            checklist2 = None
            checklist3 = None
            checklist4 = None
            checklist5 = None
            checklist6 = None
            checklist7 = None
            checklist8 = None
            checklist9 = None
            checklist10 = None
            checklist11 = None
            checklist12 = None
        try:
            grade_file = crsGrade.objects.get(studentID=stud_id)
        except crsGrade.DoesNotExist:
            grade_file = None
        if 'submit' in request.POST:
            if (request.method=='POST'):
                status=request.POST.get('slct')
                if status=='Submitted':
                    grade_file.remarks = "Submitted"
                    grade_file.save()
                elif status=='Returned':
                    grade_file.remarks = "Returned"
                    grade_file.crsFile.delete()
                    grade_file.save()
                    messages.success(request,'File is Returned, No file.')
                elif status=='Approved':
                    grade_file.remarks = "Approved"
                    grade_file.save()
        if 'feedbackBtn' in request.POST:
            fcount = 1
        if 'feedback' in request.POST:
            if (request.method=='POST'):
                grade_file.comment = request.POST.get('message')
                grade_file.save()
                messages.success(request,'Feedback is successfully sent!')
        context = {'checklist': checklist,'checklist2': checklist2,'checklist3': checklist3,'checklist4': checklist4,'checklist5': checklist5,'checklist6': checklist6, 'checklist7': checklist7,'checklist8': checklist8,'checklist9': checklist9, 'checklist10': checklist10, 'checklist11': checklist11, 'checklist12': checklist12, 'ave':ave, 'ave2': ave2, 'ave3':ave3, 'ave4':ave4, 'ave5':ave5, 'ave6':ave6, 'ave7':ave7, 'ave8' :ave8, 'ave9':ave9, 'ave10':ave10, 'ave11':ave11, 'ave12':ave12, 'stud_id': stud_id, 'grade_file':grade_file, 'fcount':fcount}
        return render(request, 'faculty/fStudents_viewStudentGrade.html', context)
    else:
        return redirect('index')


def fviewstudent(request, sched_id):
    if request.user.is_authenticated and request.user.is_faculty:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        schedule = studentScheduling.objects.get(id=sched_id)
        student = StudentInfo.objects.filter(studentSection=schedule.realsection)
        students = student.count()
        result = filters.Search(request.GET, queryset=student); student = result.qs
        context = {'result':result, 'id': id, 'info':info, 'acad': acad, 'schedule' : schedule, 'student' : student, 'students' : students}
        return render(request, 'faculty/viewstudent.html', context)
    else:
        return redirect('index')

def fViewSched(request):
    if request.user.is_authenticated and request.user.is_faculty:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        schedule = studentScheduling.objects.filter(instructor=info)
        subjects = schedule.count()
        context = {'id': id, 'info':info, 'acad': acad, 'schedule' : schedule, 'subjects' : subjects}
        return render(request, 'faculty/fViewSched.html', context)
    else:
        return redirect('index')


# ---------------------------- STUDENT VIEWS ---------------------------------

def student(request):
    if request.user.is_authenticated and request.user.is_student:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        context = {'id': id, 'info':info, 'acad': acad}
        return render(request,'student/student.html', context)
    else:
        return redirect('index')

def student_change_password(request):
    if request.user.is_authenticated and request.user.is_student:
        if (request.method=='POST'):
            form = PasswordChangeForm(request.user,request.POST)
            if form.is_valid():
                user=form.save()
                update_session_auth_hash(request, user)
                messages.success(request,'Password Updated')
                return redirect('student_profile')
            else:
                messages.error(request,'Error!')
        else:
            form = PasswordChangeForm(request.user)
        return render(request,'./student/student_change_password.html',{'form':form})
    else:
        return redirect('index')

def student_clearanceform(request):
        return render(request, 'forms/student_clearance.html') 

#---------------------------- APPLICANT VIEWS --------------------------
def applicant(request):
    return render(request,'./applicant/applicant.html')


#--------------------------- FACULTY APPLICANT VIEWS --------------------------
def applicant_facultyapplicationform(request):
    if (request.method == 'POST'):
        try:
            firstName = request.POST['firstName']
            lastName = request.POST['lastName']
            middleName = request.POST['middleName']
            email = request.POST['email']
            phoneNumber = request.POST['phoneNumber']
            department = request.POST['department']
            CV = request.FILES['CV']
            certificates = request.FILES.get('certificates')
            credentials = request.FILES.get('credentials')
            TOR = request.FILES['TOR']
            facultyApplicantInfo = FacultyApplicant(firstName=firstName,lastName=lastName,middleName=middleName,email=email,phoneNumber=phoneNumber,department=department,CV=CV, certificates=certificates, credentials=credentials, TOR=TOR)
            facultyApplicantInfo.save()
            return redirect('applicant_successfullysubmitted')
        except:
            messages.error(request,'Fill everything on the form!')
            return render(request,'./applicant/applicant_facultyapplicationform.html')
    return render(request, './applicant/applicant_facultyapplicationform.html')


def applicant_successfullysubmitted(request):
    return render(request, './applicant/applicant_successfullysubmitted.html')

def applicantrequirements(request):
    return render(request, './applicant/applicantrequirements.html')
    
def faculty_applicant(request):
    return render(request, './applicant/faculty_applicant.html')

def faculty_applicant_form(request):
    if (request.method == 'POST'):
        try:
            firstName = request.POST['firstName']
            lastName = request.POST['lastName']
            middleName = request.POST['middleName']
            email = request.POST['email']
            phoneNumber = request.POST['phoneNumber']
            CV = request.FILES['CV']
            certificates = request.FILES.get('certificates')
            credentials = request.FILES.get('credentials')
            TOR = request.FILES['TOR']
            facultyApplicantInfo = FacultyApplicant(firstName=firstName,lastName=lastName,middleName=middleName,email=email,phoneNumber=phoneNumber,CV=CV, certificates=certificates, credentials=credentials, TOR=TOR)
            facultyApplicantInfo.save()
            return redirect('faculty_applicant_form_submitted')
        except:
            messages.error(request,'Fill everything on the form!')
            return render(request,'./applicant/faculty_applicant_form.html')
    return render(request, './applicant/faculty_applicant_form.html')
    
def faculty_applicant_form_submitted(request):
    return render(request,'./applicant/faculty_applicant_form_submitted.html')


# ------------------- STUDENT APPLICANT VIEWS -------------------------------
def student_applicant(request):
    return render(request,'./applicant/student_applicant.html')

# ------------------- ADMIN SITE VIEWS -------------------------------------
def admin(request):
    if request.user.is_authenticated and request.user.is_admin:
        if (request.method == 'POST'):
            username = request.POST.get('email')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type')

        return render('admin')

def sHome(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        context = {'id': id, 'info':info, 'acad': acad}
        return render(request, 'student/sHome/sHome.html', context) 
    else:
         return redirect('index')

def sHomeNotifications(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            hd_applicant = hdApplicant.objects.get(studentID=id)
        except hdApplicant.DoesNotExist:
            hd_applicant = None
        try:
            ojt_applicant = OjtApplicant.objects.get(studentID=id)
        except OjtApplicant.DoesNotExist: 
            ojt_applicant = None
        context = {'id': id,'acad':acad, 'info':info, 'hd_applicant':hd_applicant, 'ojt_applicant': ojt_applicant}
        return render(request, 'student/sHome/sHomeNotifcations.html', context) 
    else:
         return redirect('index')

def HDNotif(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            notif_type = "HONORABLE DISMISSAL"
            feedback = hdApplicant.objects.get(studentID=id)
            description = "Submission Feedback"
        except hdApplicant.DoesNotExist:
            notif_type = "HONORABLE DISMISSAL"
            description = "No Submitted Application"
            feedback = None
        context = {'id': id,'acad':acad, 'info':info, 'feedback' : feedback, 'notif_type' : notif_type, 'description' : description }
        return render(request, 'student/sHome/sHomeNotifdetails.html', context) 
    else:
         return redirect('index')

def LOANotif(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            notif_type = "LEAVE OF ABSENCE"
            feedback = LOAApplicant.objects.get(studentID=id)
            description = "Submission Feedback"
        except LOAApplicant.DoesNotExist:
            notif_type = "LEAVE OF ABSENCE"
            description = "No Submitted Application"
            feedback = None
        context = {'id': id,'acad':acad, 'info':info, 'feedback' : feedback, 'notif_type' : notif_type, 'description' : description }
        return render(request, 'student/sHome/sHomeNotifdetails.html', context) 
    else:
         return redirect('index')

def SPNotif(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            notif_type = "STUDY PLAN"
            feedback = spApplicant.objects.get(studentID=id)
            description = "Submission Feedback"
        except spApplicant.DoesNotExist:
            notif_type = "STUDY PLAN"
            description = "No Submitted Application"
            feedback = None
        context = {'id': id,'acad':acad, 'info':info, 'feedback' : feedback, 'notif_type' : notif_type, 'description' : description }
        return render(request, 'student/sHome/sHomeNotifdetails.html', context) 
    else:
         return redirect('index')

def OJTNotif(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            notif_type = "PRACTICUM"
            feedback = OjtApplicant.objects.get(studentID=id)
            description = "Application Submission Feedback"
        except OjtApplicant.DoesNotExist:
            notif_type = "PRACTICUM"
            description = "No Submitted Application"
            feedback = None
        context = {'id': id,'acad':acad, 'info':info, 'feedback' : feedback, 'notif_type' : notif_type, 'description' : description }
        return render(request, 'student/sHome/sHomeNotifdetails.html', context) 
    else:
         return redirect('index')

def sProfile(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        context = {'id': id, 'info':info, 'acad': acad}
        return render(request, 'student/sHome/sProfile.html', context)
    else:
         return redirect('index')

def sProfileChangePass(request):
    if request.user.is_authenticated and request.user.is_student:
        if (request.method=='POST'):
            form = PasswordChangeForm(request.user,request.POST)
            if form.is_valid():
                user=form.save()
                update_session_auth_hash(request, user)
                messages.success(request,'Password Updated!')
                return redirect('sProfile')
            else:
                messages.error(request, 'Your password must contain at least 1 uppercase letter, A-Z.')
                messages.error(request, 'Your password must contain at least 1 lowercase letter, a-z.')
                messages.error(request, 'Your password contain atleast 1 symbol character')
                messages.error(request, 'Your password must have 8 minimum Characters')
                messages.error(request, 'Re-typed password must match to the new password')
        else:
            form = PasswordChangeForm(request.user)
        return render(request,'student/sHome/sProfileChangePass.html',{'form':form})
    else:
         return redirect('index')
    
def sProfileEdit(request):
    if request.user.is_authenticated and request.user.is_student:
        user = request.user
        info = request.user.studentinfo
        acad = AcademicYearInfo.objects.all
        if (request.method =='POST'):
            info.studentContact=request.POST.get('newContact')
            user.save()
            info.save()
            messages.success(request, 'Profile Updated!')
            return redirect('sProfile')        
        context = {'user': user, 'info':info, 'acad': acad}
        return render(request, 'student/sHome/sProfileEdit.html', context)
    else:
         return redirect('index')

def sChecklist(request):
    if request.user.is_authenticated and request.user.is_student:
        id = request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            checklist = currchecklist.objects.filter(owner_id=info).filter(yearTaken='1').filter(semTaken='1')
            checklist2 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='1').filter(semTaken='2')
            checklist3 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='2').filter(semTaken='1')
            checklist4 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='2').filter(semTaken='2')
            checklist5 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='3').filter(semTaken='1')
            checklist6 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='3').filter(semTaken='2')
            checklist7 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='4').filter(semTaken='1')
            checklist8 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='4').filter(semTaken='2')
            checklist9 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='5').filter(semTaken='1')
            checklist10 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='5').filter(semTaken='2')
            checklist11 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='6').filter(semTaken='1')
            checklist12 = currchecklist.objects.filter(owner_id=info).filter(yearTaken='6').filter(semTaken='2')
            count = curriculumInfo.objects.filter(counted_in_GWA=True)
            prevunitsum = 0
            prevunitsum2 = 0
            prevunitsum3 = 0
            prevunitsum4 = 0
            prevunitsum5 = 0
            prevunitsum6 = 0
            prevunitsum7 = 0
            prevunitsum8 = 0
            prevunitsum9 = 0
            prevunitsum10 = 0
            prevunitsum11 = 0
            prevunitsum12 = 0
            unitsum = 0 
            unitsum2 = 0
            unitsum3 = 0
            unitsum4 = 0
            unitsum5 = 0
            unitsum6 = 0
            unitsum7 = 0
            unitsum8 = 0
            unitsum9 = 0
            unitsum10 = 0
            unitsum11 = 0
            unitsum12 = 0
            for subj in checklist.filter(curriculumCode__in = count):
                n = float(subj.curriculumCode.subjectUnits)
                g = float(subj.subjectGrades)
                unitprod = n * g
                prevunitsum = prevunitsum+unitprod
                unitsum = unitsum + n
            if prevunitsum == 0:
                ave = 0
            else:
                ave = float(prevunitsum / unitsum)
            for subj in checklist2.filter(curriculumCode__in = count):
                n2 = float(subj.curriculumCode.subjectUnits)
                g2 = float(subj.subjectGrades)
                unitprod2 = n2 * g2
                prevunitsum2 = prevunitsum2+unitprod2
                unitsum2 = unitsum2 + n2
            if prevunitsum2 == 0:
                ave2 = 0
            else:
                ave2 = float(prevunitsum2 / unitsum2)
            for subj in checklist3.filter(curriculumCode__in = count):
                n3 = float(subj.curriculumCode.subjectUnits)
                g3 = float(subj.subjectGrades)
                unitprod3 = n3 * g3
                prevunitsum3 = prevunitsum3+unitprod3
                unitsum3 = unitsum3 + n3
            if prevunitsum3 == 0:
                ave3 = 0
            else:
                ave3 = float(prevunitsum3 / unitsum3)
            for subj in checklist4.filter(curriculumCode__in = count):
                n4 = float(subj.curriculumCode.subjectUnits)
                g4 = float(subj.subjectGrades)
                unitprod4 = n4 * g4
                prevunitsum4 = prevunitsum4+unitprod4
                unitsum4 = unitsum4 + n4
            if prevunitsum4 == 0:
                ave4 = 0
            else:
                ave4 = float(prevunitsum4 / unitsum4)
            for subj in checklist5.filter(curriculumCode__in = count):
                n5 = float(subj.curriculumCode.subjectUnits)
                g5 = float(subj.subjectGrades)
                unitprod5 = n5 * g5
                prevunitsum5 = prevunitsum5+unitprod5
                unitsum5 = unitsum5 + n5
            if prevunitsum5 == 0:
                ave5 = 0
            else:
                ave5 = float(prevunitsum5 / unitsum5)
            for subj in checklist6.filter(curriculumCode__in = count):
                n6 = float(subj.curriculumCode.subjectUnits)
                g6 = float(subj.subjectGrades)
                unitprod6 = n6 * g6
                prevunitsum6 = prevunitsum6+unitprod6
                unitsum6 = unitsum6 + n6
            if prevunitsum6 == 0:
                ave6 = 0
            else:
                ave6 = float(prevunitsum6 / unitsum6)
            for subj in checklist7.filter(curriculumCode__in = count):
                n7 = float(subj.curriculumCode.subjectUnits)
                g7 = float(subj.subjectGrades)
                unitprod7 = n7 * g7
                prevunitsum7 = prevunitsum7+unitprod7
                unitsum7 = unitsum7 + n7
            if prevunitsum7 == 0:
                ave7 = 0
            else:
                ave7 = float(prevunitsum7 / unitsum7)
            for subj in checklist8.filter(curriculumCode__in = count):
                n8 = float(subj.curriculumCode.subjectUnits)
                g8 = float(subj.subjectGrades)
                unitprod8 = n8 * g8
                prevunitsum8 = prevunitsum8+unitprod8
                unitsum8 = unitsum8 + n8
            if prevunitsum8 == 0:
                ave8 = 0
            else:
                ave8 = float(prevunitsum8 / unitsum8)
            for subj in checklist9.filter(curriculumCode__in = count):
                n9 = float(subj.curriculumCode.subjectUnits)
                g9 = float(subj.subjectGrades)
                unitprod9 = n9 * g9
                prevunitsum9 = prevunitsum9+unitprod9
                unitsum9 = unitsum9 + n9
            if prevunitsum9 == 0:
                ave9 = 0
            else:
                ave9 = float(prevunitsum9 / unitsum9)
            for subj in checklist10.filter(curriculumCode__in = count):
                n10 = float(subj.curriculumCode.subjectUnits)
                g10 = float(subj.subjectGrades)
                unitprod10 = n10 * g10
                prevunitsum10 = prevunitsum10+unitprod10
                unitsum10 = unitsum10 + n10
            if prevunitsum10 == 0:
                ave10 = 0
            else:
                ave10 = float(prevunitsum10 / unitsum10)
            for subj in checklist11.filter(curriculumCode__in = count):
                n11 = float(subj.curriculumCode.subjectUnits)
                g11 = float(subj.subjectGrades)
                unitprod11 = n11 * g11
                prevunitsum11 = prevunitsum11+unitprod11
                unitsum11 = unitsum11 + n11
            if prevunitsum11 == 0:
                ave11 = 0
            else:
                ave11 = float(prevunitsum11 / unitsum11)
            for subj in checklist12.filter(curriculumCode__in = count):
                n12 = float(subj.curriculumCode.subjectUnits)
                g12 = float(subj.subjectGrades)
                unitprod12 = n12 * g12
                prevunitsum12 = prevunitsum12+unitprod12
                unitsum12 = unitsum12 + n12
            if prevunitsum12 == 0:
                ave12 = 0
            else:
                ave12 = float(prevunitsum12 / unitsum12)
        except currchecklist.DoesNotExist:
            checklist = None
            checklist2 = None
            checklist3 = None
            checklist4 = None
            checklist5 = None
            checklist6 = None
            checklist7 = None
            checklist8 = None
            checklist9 = None
            checklist10 = None
            checklist11 = None
            checklist12 = None
        context = {'id': id, 'info': info, 'checklist': checklist, 'checklist2': checklist2,'checklist3': checklist3,'checklist4': checklist4,'checklist5': checklist5,'checklist6': checklist6,'checklist7': checklist7,'checklist8': checklist8, 'checklist9': checklist9, 'checklist10': checklist10, 'checklist11': checklist11, 'checklist12': checklist12, 'prevunitsum': prevunitsum, 'ave':ave, 'ave2': ave2, 'ave3':ave3, 'ave4':ave4, 'ave5':ave5, 'ave6':ave6, 'ave7':ave7, 'ave8' :ave8, 'ave9':ave9, 'ave10':ave10, 'ave11':ave11, 'ave12':ave12,}
        return render(request, 'student/sClassroom/sChecklist.html', context)
    else:
        return redirect('index')

def sChecklistEmptyConfirmation(request, currchecklist_id):
    if request.user.is_authenticated and request.user.is_student:
        subject = currchecklist.objects.get(id = currchecklist_id)
        if request.method =='POST':
            subject.delete()
            messages.success(request, "Successfully Deleted")
            return redirect('sChecklist')
        context = {'subj': subject}
        return render(request, 'student/sClassroom/sChecklistEmptyConfirmation.html', context)
    else:
        return redirect('index')

def sClassroom(request):
    if request.user.is_authenticated and request.user.is_student:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        schedule = studentScheduling.objects.filter(realsection=info.studentSection)
        subjects = schedule.count()
        context = {'id': id, 'info':info, 'acad': acad, 'subjects': subjects, 'sum' :sum}
        return render(request, 'student/sClassroom/sClassroom.html', context)
    else:
         return redirect('index')


def sGradeSubmission1(request):
    if request.user.is_authenticated and request.user.is_student:
        OrderFormSet = inlineformset_factory(StudentInfo, currchecklist, fields=('owner','curriculumCode', 'subjectGrades','yearTaken','semTaken'),widgets={'curriculumCode': forms.Select(attrs={"class": "form-control", "id":"instructorField", "required": True}), 'subjectGrades': forms.Select(attrs={"class": "form-control", "id":"instructorField","required": True}),'yearTaken': forms.Select(attrs={"class": "form-control", "id":"instructorField","required": True}), 'semTaken': forms.Select(attrs={"class": "form-control", "id":"instructorField","required": True})}, max_num=1, can_delete=False)
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        subjects = currchecklist.objects.filter(owner=info)
        formset = OrderFormSet(queryset=currchecklist.objects.none(), instance=info)
        for form in formset:
            form.fields['curriculumCode'].queryset = curriculumInfo.objects.filter(curriculumyear=info.studentCurriculum).filter(departmentID=info.departmentID)
        if request.method =='POST':
            formset = OrderFormSet(request.POST, instance=info)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Successfully submitted!")
                return redirect('sGradeSubmission1')
            else:
                messages.error(request, "Submission Failed!")
        context = {'formset': formset, 'subjects':subjects}
        return render(request, './student/sClassroom/sGradeSubmission1.html', context) 
    else:
         return redirect('index')
    
def sGradeSubmission2(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            crsFile = request.FILES.get('crsFile')
            try:
                grade_file = crsGrade.objects.get(studentID_id=id)
                if grade_file.remarks == "Returned":
                    if (request.method == 'POST'):
                        grade_file.crsFile = request.FILES.get('crsFile')
                        grade_file.remarks = 'Submitted'
                        grade_file.save()
                        return redirect('sGradeSubmission3') 
                else:
                    messages.error(request,'You have already submitted an application!')
                    return render(request,'student/sClassroom/sGradeSubmission2.html')
            except ObjectDoesNotExist:
                student = crsGrade(studentID=info,crsFile=crsFile)
                student.save()
                return redirect('sGradeSubmission3')
        return render(request, 'student/sClassroom/sGradeSubmission2.html')
    else:
         return redirect('index')

def sGradeSubmission3(request):
    if request.user.is_authenticated and request.user.is_student:
        return render(request, 'student/sClassroom/sGradeSubmission3.html')
    else:
         return redirect('index')

def donecrs(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            grade_file = crsGrade.objects.get(studentID_id=id)
            if grade_file.remarks == "Returned":
                return redirect('sGradeSubmission2') 
            else:
                return redirect('sGradeSubmission3') 
        except ObjectDoesNotExist:
            return redirect('sGradeSubmission1')
    else:
        return redirect('index')

def sOthers(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            hd_applicant = hdApplicant.objects.get(studentID=id)
        except hdApplicant.DoesNotExist:
            hd_applicant = None
        try:
            ojt_applicant = OjtApplicant.objects.get(studentID=id)
        except OjtApplicant.DoesNotExist: 
            ojt_applicant = None
        try:
            loa_applicant = LOAApplicant.objects.get(studentID=id)
        except LOAApplicant.DoesNotExist: 
            loa_applicant = None
        try:
            sp_applicant = spApplicant.objects.get(studentID=id)
        except spApplicant.DoesNotExist: 
            sp_applicant = None
        context = {'id': id, 'info':info, 'hd_applicant':hd_applicant, 'ojt_applicant': ojt_applicant, 'loa_applicant' : loa_applicant, 'sp_applicant': sp_applicant}
        return render(request, 'student/sOthers/sOthers.html', context)
    else:
         return redirect('index')

def sScheduleView(request):
    if request.user.is_authenticated and request.user.is_student:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        schedule = studentScheduling.objects.filter(realsection=info.studentSection)
        subjects = schedule.count()
        context = {'id': id, 'info':info, 'acad': acad, 'schedule' : schedule, 'subjects' : subjects}
        if info.studentRegStatus == "Regular":
            return render(request, 'student/sClassroom/sScheduleView.html', context)
        else:
            return render(request, 'student/sClassroom/sScheduleViewIrreg.html', context)
    else:
         return redirect('index')

def sScheduleViewOnline(request):
    if request.user.is_authenticated and request.user.is_student:
        return render(request, 'student/sClassroom/sScheduleViewOnline.html')
    else:
        return redirect('index')



def sCheclistEmptyConfirmation(request):
    if request.user.is_authenticated and request.user.is_student:
        acad = AcademicYearInfo.objects.all
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        context = {'id': id, 'info':info, 'acad': acad}
        return render(request, 'student/sClassroom/sCheclistEmptyConfirmation.html', context)
    else:
         return redirect('index')

#HD: Clearance Form Fill-Up
def sHd1(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            firstEnrollment = request.POST.get('firstEnrollment')
            studentFirstSY = request.POST.get('studentFirstSY')
            studentFirstCollege = request.POST.get('studentFirstCollege')
            lastEnrollment = request.POST.get('lastEnrollment')
            studentLastPCollege = request.POST.get('studentLastPCollege')
            studentLastPSY = request.POST.get('studentLastPSY')
            studentPurpose = request.POST.get('studentPurpose')
            studentCurrentdate = request.POST.get('studentCurrentdate')
            studentOthers = request.POST.get('studentOthers')
            try:
                applicant = hdClearanceForm.objects.get(studentID_id=id)
                if (request.method == 'POST'):
                    applicant.firstEnrollment = request.FILES.get('studentDropform')
                    applicant.studentFirstSY = request.POST.get('studentFirstSY')
                    applicant.studentFirstCollege = request.POST.get('studentFirstCollege')
                    applicant.lastEnrollment = request.POST.get('lastEnrollment')
                    applicant.studentLastPCollege = request.POST.get('studentLastPCollege')
                    applicant.studentLastPSY = request.POST.get('studentLastPSY')
                    applicant.studentPurpose = request.POST.get('studentPurpose')
                    applicant.studentCurrentdate = request.POST.get('studentCurrentdate')
                    applicant.studentOthers = request.POST.get('studentOthers')
                    applicant.save()
                    return redirect('sHd1') 
            except ObjectDoesNotExist:
                clearance = hdClearanceForm(studentID=info,firstEnrollment=firstEnrollment,studentFirstSY=studentFirstSY ,studentFirstCollege=studentFirstCollege,lastEnrollment=lastEnrollment,studentLastPCollege=studentLastPCollege,studentLastPSY=studentLastPSY,studentPurpose=studentPurpose,studentCurrentdate=studentCurrentdate,studentOthers=studentOthers)
                clearance.save()
                return redirect('sHd1') 
        return render(request, 'student/sOthers/sHd1.html', {'info':info})
    else:
            return redirect('index')


#HD Clearance to PDF
def Student_Clearance(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            obj = hdClearanceForm.objects.get(studentID=info)
            context = {
                'id': id, 
                'info':info,
                'firstEnrollment': obj.firstEnrollment,
                'studentFirstSY': obj.studentFirstSY,
                'studentFirstCollege': obj.studentFirstCollege,
                'lastEnrollment': obj.lastEnrollment, 
                'studentLastPCollege': obj.studentLastPCollege,
                'studentLastPSY': obj.studentLastPSY,
                'studentPurpose': obj.studentPurpose,
                'studentOthers': obj.studentOthers,
                'studentID' : obj.studentID_id,
                'studentCurrentdate' : obj.studentCurrentdate
                }
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] ='filename="StudentClearance_%s.pdf"' %(info.studentID)
            # find the template and render it.
            template = get_template('forms/student_clearance.html')
            html = template.render(context)
            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=response)
            # if error then show some funy view
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
        except hdClearanceForm.DoesNotExist:
            messages.error(request,'No Copy Yet')
            return redirect('sHd1')
    else:
            return redirect('index')



def sHd2(request):
    if request.user.is_authenticated and request.user.is_student:
        context={'file':HD_DroppingForm.objects.all()}
        return render(request, 'student/sOthers/sHd2.html', context)
    else:
        return redirect('index')

def HD_DownloadDF(request,path):
    file_path=os.path.join(settings.MEDIA_ROOT,path)
    if os.path.exists(file_path):
        with open(file_path,'rb')as fh:
            response=HttpResponse(fh.read(),content_type="application/Admin_Upload")
            response['Content-Disposition']='inline;filename'+os.path.basename(file_path)
            return response
    raise Http404

def sHd3(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            studentSchool = request.POST.get('studentSchool')
            studentSchooladdress = request.POST.get('studentSchooladdress')
            studentHomeaddress = request.POST.get('studentHomeaddress')
            studentCollege = request.POST.get('studentCollege')
            studentCredentials = request.POST.get('studentCredentials')
            studentFirstSY = request.POST.get('studentFirstSY')
            studentLastPSY = request.POST.get('studentLastPSY')
            studentNoOfSem = request.POST.get('studentNoOfSem')
            studentDegree = request.POST.get('studentDegree')
            studentMonth = request.POST.get('studentMonth')
            studentDay = request.POST.get('studentDay')
            studentYear = request.POST.get('studentYear')
            studentCurrentdate = request.POST.get('studentCurrentdate')
            try:
                applicant = hdTransferCert.objects.get(studentID_id=id)
                if (request.method == 'POST'):
                    applicant.studentSchool = request.POST.get('studentSchool')
                    applicant.studentSchooladdress = request.POST.get('studentSchooladdress')
                    applicant.studentHomeaddress = request.POST.get('studentHomeaddress')
                    applicant.studentCollege = request.POST.get('studentCollege')
                    applicant.studentCredentials = request.POST.get('studentCredentials')
                    applicant.studentFirstSY = request.POST.get('studentFirstSY')
                    applicant.studentLastPSY = request.POST.get('studentLastPSY')
                    applicant.studentNoOfSem = request.POST.get('studentNoOfSem')
                    applicant.studentDegree = request.POST.get('studentDegree')
                    applicant.studentMonth = request.POST.get('studentMonth')
                    applicant.studentDay = request.POST.get('studentDay')
                    applicant.studentYear = request.POST.get('studentYear')
                    applicant.studentCurrentdate = request.POST.get('studentCurrentdate')
                    applicant.save()
                    return redirect('sHd3') 
            except ObjectDoesNotExist:
                transfer = hdTransferCert(studentID=info,studentSchool=studentSchool,studentSchooladdress=studentSchooladdress ,studentHomeaddress=studentHomeaddress,studentCollege=studentCollege,studentCredentials=studentCredentials,studentFirstSY=studentFirstSY,studentLastPSY=studentLastPSY,studentNoOfSem=studentNoOfSem,studentDegree=studentDegree,studentMonth=studentMonth,studentDay=studentDay,studentYear=studentYear,studentCurrentdate=studentCurrentdate)
                transfer.save()
        return render(request, 'student/sOthers/sHd3.html', {'info':info})
    else:
        return redirect('index')

#HD Transfer Cert Fill-Up
def Student_Transfer(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            obj = hdTransferCert.objects.get(studentID=info)
            context = {
                'id': id, 
                'info':info,
                'studentSchool': obj.studentSchool,
                'studentSchooladdress': obj.studentSchooladdress,
                'studentHomeaddress': obj.studentHomeaddress,
                'studentCollege': obj.studentCollege, 
                'studentCredentials': obj.studentCredentials,
                'studentFirstSY': obj.studentFirstSY,
                'studentLastPSY': obj.studentLastPSY,
                'studentNoOfSem': obj.studentNoOfSem,
                'studentDegree': obj.studentDegree,
                'studentMonth': obj.studentMonth,
                'studentDay': obj.studentDay,
                'studentID' : obj.studentID_id,
                'studentYear' : obj.studentYear
                }
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] =' filename="StudentTransfer_%s.pdf"' %(info.studentID)
            # find the template and render it.
            template = get_template('forms/TC_Template.html')
            html = template.render(context)
            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=response)
            # if error then show some funy view
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
        except hdTransferCert.DoesNotExist:
            messages.error(request,'No Copy Yet')
            return redirect('sHd3')
    else:
        return redirect('index')


def sHd4(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            studentDropform = request.FILES.get('studentDropform')
            studentClearanceform = request.FILES.get('studentClearanceform') 
            studentHdletter = request.FILES.get('studentHdletter')
            stdParentsig = request.FILES.get('stdParentsig')
            studentTransfercert = request.FILES.get('studentTransfercert')
            studentGrades = request.FILES.get('studentGrades')
            hd_dateSubmitted = timezone.now()
            try:
                applicant = hdApplicant.objects.get(studentID_id=id)
                if applicant.remarks == "Returned":
                    if (request.method == 'POST'):
                        applicant.studentDropform = request.FILES.get('studentDropform')
                        applicant.studentClearanceform = request.FILES.get('studentClearanceform')
                        applicant.studentHdletter = request.FILES.get('studentHdletter')
                        applicant.stdParentsig = request.FILES.get('stdParentsig')
                        applicant.studentTransfercert = request.FILES.get('studentTransfercert')
                        applicant.studentGrades = request.FILES.get('studentGrades')
                        applicant.remarks = 'Submitted'
                        applicant.hd_dateSubmitted = timezone.now()
                        applicant.save()
                        return redirect('sHd5') 
                else:
                    messages.error(request,'You have already submitted an application!')
                    return render(request,'student/sOthers/sHd4.html')
            except ObjectDoesNotExist:
                hd_applicants = hdApplicant(studentID=info,studentDropform=studentDropform,studentClearanceform =studentClearanceform ,studentHdletter=studentHdletter,studentGrades=studentGrades,studentTransfercert=studentTransfercert, stdParentsig=stdParentsig,hd_dateSubmitted=hd_dateSubmitted)
                hd_applicants.save()
                return redirect('sHd5')
        return render(request, 'student/sOthers/sHd4.html')
    else:
        return redirect('index')
     

def sHd5(request):
    if request.user.is_authenticated and request.user.is_student:
        return render(request, 'student/sOthers/sHd5.html')
    else:
        return redirect('index')

def doneHd(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            applicant = hdApplicant.objects.get(studentID_id=id)
            if applicant.remarks == "Returned":
                return redirect('sHd4') 
            else:
                return redirect('sHd5') 
        except ObjectDoesNotExist:
            return redirect('sHd1')
    else:
        return redirect('index')

def sLoa1(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            firstEnrollment2 = request.POST.get('firstEnrollment2')
            studentFirstSY2 = request.POST.get('studentFirstSY2')
            studentFirstCollege2 = request.POST.get('studentFirstCollege2')
            lastEnrollment2 = request.POST.get('lastEnrollment2')
            studentLastPCollege2 = request.POST.get('studentLastPCollege2')
            studentLastPSY2 = request.POST.get('studentLastPSY2')
            studentPurpose2 = request.POST.get('studentPurpose2')
            studentOthers2 = request.POST.get('studentOthers2')
            studentCurrentdate2 = request.POST.get('studentCurrentdate2')
            try:
                applicant = loaClearanceForm.objects.get(studentID_id=id)
                if (request.method == 'POST'):
                    applicant.firstEnrollment2 = request.POST.get('firstEnrollment2')
                    applicant.studentFirstSY2 = request.POST.get('studentFirstSY2')
                    applicant.studentFirstCollege2 = request.POST.get('studentFirstCollege2')
                    applicant.lastEnrollment2 = request.POST.get('lastEnrollment2')
                    applicant.studentLastPCollege2 = request.POST.get('studentLastPCollege2')
                    applicant.studentLastPSY2 = request.POST.get('studentLastPSY2')
                    applicant.studentPurpose2 = request.POST.get('studentPurpose2')
                    applicant.studentOthers2 = request.POST.get('studentOthers2')
                    applicant.studentCurrentdate2 = request.POST.get('studentCurrentdate2')
                    applicant.save()
                    return redirect('sLoa1') 
            except ObjectDoesNotExist:
                clearance = loaClearanceForm(studentID=info,firstEnrollment2=firstEnrollment2,studentFirstSY2=studentFirstSY2 ,studentFirstCollege2=studentFirstCollege2,lastEnrollment2=lastEnrollment2,studentLastPCollege2=studentLastPCollege2,studentLastPSY2=studentLastPSY2,studentPurpose2=studentPurpose2,studentOthers2=studentOthers2,studentCurrentdate2=studentCurrentdate2)
                clearance.save()
                return redirect('sLoa1') 
        return render(request, 'student/sOthers/sLoa1.html', {'info': info})
    else:
        return redirect('index')

def Loa_Clearance(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            obj = loaClearanceForm.objects.get(studentID=info)
            context = {
                'id': id, 
                'info':info,
                'firstEnrollment2': obj.firstEnrollment2,
                'studentFirstSY2': obj.studentFirstSY2,
                'studentFirstCollege2': obj.studentFirstCollege2,
                'lastEnrollment2': obj.lastEnrollment2, 
                'studentLastPCollege2': obj.studentLastPCollege2,
                'studentLastPSY2': obj.studentLastPSY2,
                'studentPurpose2': obj.studentPurpose2,
                'studentOthers2': obj.studentOthers2,
                'studentID' : obj.studentID_id,
                'studentCurrentdate2' : obj.studentCurrentdate2
                }
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] ='filename="LoaClearance_%s.pdf"' %(info.studentID)
            # find the template and render it.
            template = get_template('forms/loa_clearance.html')
            html = template.render(context)
            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=response)
            # if error then show some funy view
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
        except loaClearanceForm.DoesNotExist:
            messages.error(request,'No Copy Yet')
            return redirect('sLoa1')
    else:
        return redirect('index')

def sLoa2(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            dof = request.POST.get('dof')
            genave = request.POST.get('genave')
            sem = request.POST.get('sem')
            sy = request.POST.get('sy')
            sem2 = request.POST.get('sem2')
            sy2 = request.POST.get('sy2')
            reason = request.POST.get('reason')
            try:
                applicant = loaForm.objects.get(studentID_id=id)
                if (request.method == 'POST'):
                    applicant.dof = request.POST.get('dof')
                    applicant.genave = request.POST.get('genave')
                    applicant.sem = request.POST.get('sem')
                    applicant.sy = request.POST.get('sy')
                    applicant.sem2 = request.POST.get('sem2')
                    applicant.sy2 = request.POST.get('sy2')
                    applicant.reason = request.POST.get('reason')
                    applicant.save()
                    return redirect('sLoa2') 
            except ObjectDoesNotExist:
                StudentLoaForm = loaForm(studentID=info,dof=dof, genave=genave, sem=sem, sy=sy, sem2=sem2, sy2=sy2, reason=reason)
                StudentLoaForm.save()
                return redirect('sLoa2') 
        return render(request, 'student/sOthers/sLoa2.html', {'info': info})
    else:
        return redirect('index')

def Loa_Form(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            obj = loaForm.objects.get(studentID=info)
            #obj = Student.objects.get(id=studentid)
            context = {
            'id': id, 
                'info':info,
                'dof': obj.dof,
                'genave': obj.genave,
                'sem': obj.sem,
                'sy': obj.sy,
                'sem2': obj.sem2,
                'sy2': obj.sy2,
                'reason' : obj.reason,
                }
            # Create a Django response object, and specify content_type as pdf
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] ='filename="LoaForm_%s.pdf"' %(info.studentID)
            # find the template and render it.
            template = get_template('forms/LOAForm.html')
            html = template.render(context)
            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=response)
            # if error then show some funy view
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response
        except loaForm.DoesNotExist:
            messages.error(request,'No Copy Yet')
            return redirect('sLoa2')
    else:
        return redirect('index')


def sLoa3(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            studentLOAClearanceform = request.FILES.get('studentLOAClearanceform')
            studentStudyplan = request.FILES.get('studentStudyplan')
            studentLOAletter = request.FILES.get('studentLOAletter')
            studentLOAFORM = request.FILES.get('studentLOAFORM')
            studentChecklist = request.FILES.get('studentChecklist')
            now = timezone.now()
            try:
                applicant = LOAApplicant.objects.get(studentID_id=id)
                if applicant.remarks == "Returned":
                    if (request.method == 'POST'):
                        applicant.studentLOAClearanceform = request.FILES.get('studentLOAClearanceform')
                        applicant.studentStudyplan = request.FILES.get('studentStudyplan')
                        applicant.studentLOAletter = request.FILES.get('studentLOAletter')
                        applicant.studentLOAFORM = request.FILES.get('studentLOAFORM')
                        applicant.studentChecklist = request.FILES.get('studentChecklist')
                        applicant.remarks = 'Submitted'
                        applicant.LOA_dateSubmitted = timezone.now()
                        applicant.save()
                        return redirect('sLoa4') 
                else:
                    messages.error(request,'You have already submitted an application!')
                    return render(request,'student/sOthers/sLoa3.html')
            except ObjectDoesNotExist:
                loaApplicant = LOAApplicant(studentID=info,studentLOAClearanceform =studentLOAClearanceform,studentLOAFORM =studentLOAFORM ,studentLOAletter =studentLOAletter,studentChecklist=studentChecklist,studentStudyplan=studentStudyplan,LOA_dateSubmitted=now)
                loaApplicant.save()
                return redirect('sLoa4')
        return render(request, 'student/sOthers/sLoa3.html')
    else:
        return redirect('index')

def sLoa4(request):
    if request.user.is_authenticated and request.user.is_student:
        return render(request, 'student/sOthers/sLoa4.html')
    else:
        return redirect('index')

def doneLoa(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            applicant = LOAApplicant.objects.get(studentID_id=id)
            if applicant.remarks == "Returned":
                return redirect('sLoa3') 
            else:
                return redirect('sLoa4') 
        except ObjectDoesNotExist:
            return redirect('sLoa1')
    else:
        return redirect('index')


#---------------------------- Ojt Applicant --------------------------
def sPracticum1(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            ojtResume = request.FILES.get("resume")
            ojtRecLetter = request.FILES.get("recletter")
            ojtWaiver = request.FILES.get("waiver")
            ojtAcceptForm = request.FILES.get("acceptform")
            ojtCompanyProfile = request.FILES.get("companyprofile")
            ojtCompanyId = request.FILES.get("companyid")
            ojtMedcert =   request.FILES.get("medcert")
            ojt_dateSubmitted = timezone.now()
            try:
                applicant = OjtApplicant.objects.get(studentID_id=id)
                if applicant.remarks == "Returned":
                    if (request.method == 'POST'):
                        applicant.ojtResume = request.FILES.get('resume')
                        applicant.ojtRecLetter = request.FILES.get('recletter')
                        applicant.ojtWaiver = request.FILES.get('waiver')
                        applicant.ojtAcceptForm = request.FILES.get('acceptform')
                        applicant.ojtCompanyProfile = request.FILES.get('companyprofile')
                        applicant.ojtCompanyId = request.FILES.get('companyid')
                        applicant.ojtMedcert = request.FILES.get('medcert')
                        applicant.remarks = 'Submitted'
                        applicant.ojt_dateSubmitted = timezone.now()
                        applicant.save()
                        return redirect('sPracticum2') 
                else:
                    messages.error(request,'You have already submitted an application!')
                    return render(request,'student/sOthers/sPracticum1.html')
            except ObjectDoesNotExist:
                ojtApplicant = OjtApplicant(studentID=info, ojtResume=ojtResume, ojtRecLetter=ojtRecLetter, ojtWaiver=ojtWaiver, ojtAcceptForm=ojtAcceptForm, ojtCompanyProfile=ojtCompanyProfile, ojtCompanyId=ojtCompanyId, ojtMedcert=ojtMedcert,ojt_dateSubmitted=ojt_dateSubmitted)
                ojtApplicant.save()
                return redirect('sPracticum2')
        return render(request, 'student/sOthers/sPracticum1.html')
    else:
            return redirect('index')

def sPracticum2(request):
    if request.user.is_authenticated and request.user.is_student:
        return render(request,'student/sOthers/sPracticum2.html')
    else:
            return redirect('index')
            

def donepracticum(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if info.studentYearlevel == "4":
            try:
                applicant = LOAApplicant.objects.get(studentID_id=id)
                if applicant.remarks == "Returned":
                    return redirect('sPracticum1') 
                else:
                    return redirect('sPracticum2') 
            except ObjectDoesNotExist:
                return redirect('sPracticum1')
        else:
            try:
                hd_applicant = hdApplicant.objects.get(studentID=id)
            except hdApplicant.DoesNotExist:
                hd_applicant = None
            try:
                ojt_applicant = OjtApplicant.objects.get(studentID=id)
            except OjtApplicant.DoesNotExist: 
                ojt_applicant = None
            try:
                loa_applicant = LOAApplicant.objects.get(studentID=id)
            except LOAApplicant.DoesNotExist: 
                loa_applicant = None
            context = {'hd_applicant' : hd_applicant , 'ojt_applicant' : ojt_applicant , 'loa_applicant' :loa_applicant}
            messages.error(request,'Not Eligible!')
            return render(request,'student/sOthers/sOthers.html', context)
    else:
        return redirect('index')

def donesp(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        try:
            applicant = spApplicant.objects.get(studentID_id=id)
            if applicant.remarks == "Returned":
                return redirect('stdplnyr') 
            else:
                return redirect('stdplncs') 
        except ObjectDoesNotExist:
            return redirect('stdplnyr')
    else:
        return redirect('index')

# ------------------- STUDENT APPLICANT VIEWS // CHAIRPERSON-------------------------------
def student_applicant(request):
    return render(request,'./applicant/student_applicant.html')

def hd_request(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        hdapplicant = hdApplicant.objects.filter(studentID__in=student)
        return render(request, 'chairperson/Others/cOthers-hd.html', {"hdapplicant":hdapplicant, 'info':info})

def hd_general(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        hd_masterlist = hdApplicant.objects.filter(studentID__in=student)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            hd_masterlist = hd_masterlist.filter(Q(studentID__studentUser__lastName__icontains=searchthis_query) | Q(studentID__studentID__icontains=searchthis_query)| Q(studentID__studentUser__firstName__icontains=searchthis_query)| Q(studentID__studentUser__middleName__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = {
        'info' : info,
        'hd_masterlist' : hd_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-hd.html', context)

def hd_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        hd_masterlist = hdApplicant.objects.filter(studentID__in=student)
        hd_returned = hdApplicant.objects.filter(studentID__in=student).filter(remarks="Returned")
        hd_submitted = hdApplicant.objects.filter(studentID__in=student).filter(remarks="Submitted")
        hd_forwarded = hdApplicant.objects.filter(studentID__in=student).filter(remarks="Forwarded")
        hd_inprogress = hdApplicant.objects.filter(studentID__in=student).filter(remarks="In Progress")
        hd_complete = hdApplicant.objects.filter(studentID__in=student).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'hd_submitted' : hd_submitted,
        'hd_returned' : hd_returned,
        'hd_forwarded' : hd_forwarded,
        'hd_inprogress' : hd_inprogress,
        'hd_complete' : hd_complete,
        'hd_masterlist' : hd_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-hd-Master.html', context)


def hd_view(request,hd_id):
    if request.method == 'GET':
        hd_applicant = hdApplicant.objects.get(pk=hd_id)
        return render(request, 'chairperson/Others/cOthers-hdView.html', {'hd_applicant':hd_applicant})
    elif request.method == "POST":
        hd_applicant = hdApplicant.objects.get(pk=hd_id)
        hd_stat = request.POST.get('slct')
        hd_applicant.remarks = hd_stat
        hd_applicant.save()
        return redirect('cOthers-hd')


def feedback(request,hd_id):
    feed = hdApplicant.objects.get(pk=hd_id)
    return render(request, 'chairperson/Others/feedback.html', {'feed':feed})

def message(request, hd_id):
    if request.method == 'GET':
        feed = hdApplicant.objects.get(pk=hd_id)
        return render (request, 'chairperson/Others/feedback.html', {'feed' : feed})
    elif request.method == 'POST':
        comms = hdApplicant.objects.get(pk=hd_id)
        comm = request.POST.get('actionRequired')
        comms.comment = comm
        comms.save()
        messages.success(request, 'Feedback Succesfully Sent!')
        return HttpResponseRedirect(reverse('feedback', args=(hd_id,)))


def del_allHD(request, hd_id):
    hd_applicant = hdApplicant.objects.get(pk=hd_id)
    hd_applicant.studentDropform.delete()
    hd_applicant.studentClearanceform.delete()
    hd_applicant.studentTransfercert.delete()
    hd_applicant.studentHdletter.delete()
    hd_applicant.studentGrades.delete()
    hd_applicant.stdParentsig.delete()
    return HttpResponseRedirect(reverse('cOthers-hdView', args=(hd_id,)))

def sendingemailHD(request, hd_id):
    sends = hdApplicant.objects.get(pk=hd_id)
    message = ''
    subject = ''
    mail_id = 'cperson.dummy@gmail.com'
    email = EmailMessage(subject, message, EMAIL_HOST_USER, [mail_id])
    email.content_subtype = 'html'

    try:
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentDropform.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentClearanceform.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentTransfercert.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentHdletter.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentGrades.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.stdParentsig.name))
        email.send()
        messages.success(request,"Successfully sent!")

        return HttpResponseRedirect(reverse('cOthers-hdView', args=(hd_id,)))
    except PermissionError:
        return HttpResponse("invalid")

#Study plan applicant

def pta_request(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        parttime = FacultyInfo.objects.filter(departmentID=info.departmentID).filter(facultyWorkstatus="Part-Time")
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            parttime = parttime.filter(Q(facultyUser__lastName__icontains=searchthis_query) | Q(facultyID__icontains=searchthis_query)| Q(facultyUser__firstName__icontains=searchthis_query)| Q(facultyUser__middleName__icontains=searchthis_query)).distinct()
        return render(request, 'chairperson/Others/cOthers-partTime.html', {'parttime':parttime, 'info':info})

def pta_view(request, pt_id):
    if request.method == 'GET':
        part_time = FacultyInfo.objects.get(facultyUser=pt_id)
        return render(request, 'chairperson/Others/cOthers-partTimeView.html', {'part_time': part_time})

def sp_request(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        spapplicant = spApplicant.objects.filter(studentID__in=student)
        return render(request, 'chairperson/Others/cOthers-studyPlan.html', {'spapplicant':spapplicant, 'info':info})

def sp_general(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        sp_masterlist = spApplicant.objects.filter(studentID__in=student)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            sp_masterlist  = sp_masterlist.filter(Q(studentID__studentUser__lastName__icontains=searchthis_query) | Q(studentID__studentID__icontains=searchthis_query)| Q(studentID__studentUser__firstName__icontains=searchthis_query)| Q(studentID__studentUser__middleName__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = {
        'info' : info,
        'sp_masterlist' : sp_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-studyPlan.html', context)

def sp_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        sp_masterlist = spApplicant.objects.filter(studentID__in=student)
        sp_returned = spApplicant.objects.filter(studentID__in=student).filter(remarks="Returned")
        sp_submitted = spApplicant.objects.filter(studentID__in=student).filter(remarks="Submitted")
        sp_forwarded = spApplicant.objects.filter(studentID__in=student).filter(remarks="Forwarded")
        sp_inprogress = spApplicant.objects.filter(studentID__in=student).filter(remarks="In Progress")
        sp_complete = spApplicant.objects.filter(studentID__in=student).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'sp_submitted' : sp_submitted,
        'sp_returned' : sp_returned,
        'sp_forwarded' : sp_forwarded,
        'sp_inprogress' : sp_inprogress,
        'sp_complete' : sp_complete,
        'sp_masterlist' : sp_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-studyPlan-Master.html', context)


def sp_view(request,sp_id):
    if request.method == 'GET':
        sp_applicant = spApplicant.objects.get(pk=sp_id)
        return render(request, 'chairperson/Others/cOthers-studyPlanView.html', {'sp_applicant':sp_applicant})
    elif request.method == "POST":
        sp_applicant = spApplicant.objects.get(pk=sp_id)
        sp_stat = request.POST.get('slct')
        sp_applicant.remarks = sp_stat
        sp_applicant.save()
        return redirect('cOthers-studyPlan')

def del_allSP(request, sp_id):
    try:
        sp_applicant = spApplicant.objects.get(pk=sp_id)
        deletestudyplan = studyPlan.objects.get(studentinfo=sp_applicant.studentID)
        deletestudyplan.delete()
        sp_applicant.sdplan.delete()
    except studyPlan.DoesNotExist:
        deletestudyplan = None
    return HttpResponseRedirect(reverse('cOthers-studyPlanView', args=(sp_id,)))


def feedbacksp(request,sp_id):
    feed = spApplicant.objects.get(pk=sp_id)
    return render(request, 'chairperson/Others/feedbacksp.html', {'feed':feed})

def messagesp(request, sp_id):
    student = spApplicant.objects.get(pk=sp_id)
    msg = request.POST.get('actionRequired')
    student.comment = msg
    student.save()
    messages.success(request,'Feedback Successfully Sent!')
    return HttpResponseRedirect(reverse('cOthers-studyPlanView', args=(sp_id,)))

#VIEW LIST OF LOA APPLICANTS
def loa_list(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        loas_list = LOAApplicant.objects.filter(studentID__in=student)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            loas_list = loas_list.filter(Q(studentID__studentUser__lastName__icontains=searchthis_query) | Q(studentID__studentID__icontains=searchthis_query)| Q(studentID__studentUser__firstName__icontains=searchthis_query)| Q(studentID__studentUser__middleName__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = {
        'info' : info,
        'loas_list' : loas_list,
        }
        return render (request, 'chairperson/Others/cOthers-loa.html', context)

def loa_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        loas_masterlist = LOAApplicant.objects.filter(studentID__in=student)
        loas_returned = LOAApplicant.objects.filter(studentID__in=student).filter(remarks="Returned")
        loas_submitted = LOAApplicant.objects.filter(studentID__in=student).filter(remarks="Submitted")
        loas_forwared = LOAApplicant.objects.filter(studentID__in=student).filter(remarks="Forwarded")
        loas_inprogress = LOAApplicant.objects.filter(studentID__in=student).filter(remarks="In Progress")
        loas_complete = LOAApplicant.objects.filter(studentID__in=student).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'loas_masterlist' : loas_masterlist,
        'loas_submitted' : loas_submitted,
        'loas_returned' : loas_returned,
        'loas_forwarded' : loas_forwared,
        'loas_inprogress' : loas_inprogress,
        'loas_complete' : loas_complete,
        
        }
        return render (request, 'chairperson/Others/cOthers-loa-Master.html', context)


# VIEW LOA REQUEST OF STUDENT
def loa_view(request, loa_id):
    if request.method == 'GET':
        loaview = LOAApplicant.objects.get(pk=loa_id)
        return render(request, 'chairperson/Others/cOthers-loaView.html', {'loaview' : loaview})
    elif request.method == 'POST':
        loaview = LOAApplicant.objects.get(pk=loa_id)
        statform = request.POST.get('slct')
        loaview.remarks = statform
        loaview.save()
        return redirect ('cOthers-loa')

# FOR LOA FEEDBACK        
def Loa_feedback(request, loa_id):
    if request.method == 'GET':
        loa_feedback = LOAApplicant.objects.get(pk=loa_id)
        return render (request, 'chairperson/Others/cOthers-loa-feedback.html', {'loa_feedback' : loa_feedback})
    elif request.method == 'POST':
        comms = LOAApplicant.objects.get(pk=loa_id)
        comm = request.POST.get('actionRequired')
        comms.comment = comm
        comms.save()
        messages.success(request, 'Feedback Succesfully Sent!')
        return HttpResponseRedirect(reverse('cOthers-loa-feedback', args=(loa_id,)))

# FOR LOA GENERATE CSW
def loa_csw(request, loa_id):
    Loa_csw = LOAApplicant.objects.get(pk=loa_id)
    if Loa_csw.studentID.departmentID.courseName == 'BSIT':
        return render (request, 'chairperson/Others/cOthers-loa-itcsw.html', {'Loa_csw' : Loa_csw})
    elif Loa_csw.studentID.departmentID.courseName == 'BSEE':
        return render (request, 'chairperson/Others/cOthers-loa-eecsw.html', {'Loa_csw' : Loa_csw})
 
# FOR ATTACHMENT OF FILES IN CSW
def attach(request, attach_id):
    if request.method == 'POST':
        if request.POST.get("loa-attach"):
            signature = LOAApplicant.objects.get(pk=attach_id)
            request.session['_loa_data'] = request.POST
            sign1 = request.FILES.get('cSignatureFile1')
            sign2 = request.FILES.get('cSignatureFile2')
            signature.signature1 = sign1
            signature.signature2 = sign2
            signature.save()  
            messages.success(request, 'Succesfully Attached!')  
            return HttpResponseRedirect(reverse('cOthers-loa-csw', args=(attach_id,))) 

        elif request.POST.get("shifter-attach"):
            signature = ShifterApplicant.objects.get(pk=attach_id)
            request.session['_shifter_data'] = request.POST
            sign1 = request.FILES.get('cSignatureFile1')
            sign2 = request.FILES.get('cSignatureFile2')
            signature.signature1 = sign1
            signature.signature2 = sign2
            signature.save()  
            messages.success(request, 'Succesfully Attached!')  
            return HttpResponseRedirect(reverse('cOthers-shifter-csw', args=(attach_id,))) 

        elif request.POST.get("transfer-attach"):
                signature = TransfereeApplicant.objects.get(pk=attach_id)
                request.session['_transfer_data'] = request.POST
                sign1 = request.FILES.get('cSignatureFile1')
                sign2 = request.FILES.get('cSignatureFile2')
                signature.signature1 = sign1
                signature.signature2 = sign2
                signature.save()  
                messages.success(request, 'Succesfully Attached!')  
                return HttpResponseRedirect(reverse('cOthers-transferee-csw', args=(attach_id,))) 
    
#RENDER HTML LOA CSW TO PDF
def loa_Pdf(request, loa_id):
    try:
        pdf1 = LOAApplicant.objects.get(pk=loa_id)
        if pdf1.studentID.departmentID.courseName == 'BSIT':
            data = request.session.get('_loa_data')

            template = get_template('chairperson/CSW/it_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['actionRequired'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/it_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "IT_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")

        elif pdf1.studentID.departmentID.courseName == 'BSEE':
            data = request.session.get('_loa_data')

            template = get_template('chairperson/CSW/ee_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['action'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/ee_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "EE_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")
    except:
        return HttpResponse("Not found please attach first")

# FOR DELETING LOA FILES
def del_allLOA(request, loa_id):
    LOA_applicant = LOAApplicant.objects.get(pk=loa_id)
    LOA_applicant.studentLOAClearanceform.delete()
    LOA_applicant.studentStudyplan.delete()
    LOA_applicant.studentLOAletter.delete()
    LOA_applicant.studentLOAFORM.delete()
    LOA_applicant.studentChecklist.delete()
    messages.success(request, 'Files Succesfully Returned!')  
    return HttpResponseRedirect(reverse('cOthers-loaView', args=(loa_id,)))


def ojt_list(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        ojtapplicant = OjtApplicant.objects.filter(studentID__in=student)
        return render(request, 'chairperson/Others/cOthers-ojt.html', {"ojtapplicant":ojtapplicant, 'info':info})

def ojt_general(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        ojt_masterlist = OjtApplicant.objects.filter(studentID__in=student)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            ojt_masterlist  = ojt_masterlist.filter(Q(studentID__studentUser__lastName__icontains=searchthis_query) | Q(studentID__studentID__icontains=searchthis_query)| Q(studentID__studentUser__firstName__icontains=searchthis_query)| Q(studentID__studentUser__middleName__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = {
        'info' : info,
        'ojt_masterlist' : ojt_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-ojt.html', context)

def ojt_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        student = StudentInfo.objects.filter(departmentID=info.departmentID)
        ojt_masterlist = OjtApplicant.objects.filter(studentID__in=student)
        ojt_returned = OjtApplicant.objects.filter(studentID__in=student).filter(remarks="Returned")
        ojt_submitted = OjtApplicant.objects.filter(studentID__in=student).filter(remarks="Submitted")
        ojt_forwared = OjtApplicant.objects.filter(studentID__in=student).filter(remarks="Forwarded")
        ojt_inprogress = OjtApplicant.objects.filter(studentID__in=student).filter(remarks="In Progress")
        ojt_complete = OjtApplicant.objects.filter(studentID__in=student).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'ojt_submitted' : ojt_submitted,
        'ojt_returned' : ojt_returned,
        'ojt_forwarded' : ojt_forwared,
        'ojt_inprogress' : ojt_inprogress,
        'ojt_complete' : ojt_complete,
        'ojt_masterlist' : ojt_masterlist,
        }
        return render (request, 'chairperson/Others/cOthers-ojt-Master.html', context)


def ojt_view(request,ojt_id):
    if request.method == 'GET':
        ojt_applicant = OjtApplicant.objects.get(pk=ojt_id)
        return render(request, 'chairperson/Others/cOthers-ojtView.html', {'ojt_applicant':ojt_applicant})
    elif request.method == "POST":
        ojt_applicant = OjtApplicant.objects.get(pk=ojt_id)
        ojt_stat = request.POST.get('slct')
        ojt_applicant.remarks = ojt_stat
        ojt_applicant.save()
        return redirect('cOthers-ojt')

def ojt_feedback(request,ojt_id):
    feed = OjtApplicant.objects.get(pk=ojt_id)
    return render(request, 'chairperson/Others/ojt_feedback.html', {'feed':feed})

def ojt_message(request, ojt_id):
    if request.method == 'GET':
        feed = OjtApplicant.objects.get(pk=ojt_id)
        return render (request, 'chairperson/Others/ojt_feedback.html', {'feed' : feed})
    elif request.method == 'POST':
        comms = OjtApplicant.objects.get(pk=ojt_id)
        comm = request.POST.get('actionRequired')
        comms.comment = comm
        comms.save()
        messages.success(request, 'Feedback Succesfully Sent!')
        return HttpResponseRedirect(reverse('ojt_feedback', args=(ojt_id,)))

def del_allojt(request,ojt_id):
    ojt_applicant = OjtApplicant.objects.get(pk=ojt_id)
    ojt_applicant.ojtResume.delete()
    ojt_applicant.ojtRecLetter.delete()
    ojt_applicant.ojtWaiver.delete()
    ojt_applicant.ojtAcceptForm.delete()
    ojt_applicant.ojtCompanyProfile.delete()
    ojt_applicant.ojtMedcert.delete()
    ojt_applicant.ojtCompanyId.delete()
    return HttpResponseRedirect(reverse('cOthers-ojtView', args=(ojt_id,)))

def sendingemailOJT(request, ojt_id):
    sends = OjtApplicant.objects.get(pk=ojt_id)
    message = ''
    subject = ''
    mail_id = 'cperson.dummy@gmail.com'
    email = EmailMessage(subject, message, EMAIL_HOST_USER, [mail_id])
    email.content_subtype = 'html'

    try:
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtResume.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtRecLetter.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtWaiver.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtAcceptForm.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtCompanyProfile.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtMedcert.name))
        email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.ojtCompanyId.name))
        email.send()
        messages.success(request,"Successfully sent!")
        return HttpResponseRedirect(reverse('cOthers-ojtView', args=(ojt_id,)))
    except PermissionError:
        return HttpResponse("invalid")
 
# FOR VIEWING SHIFTER LIST
def shifter_list(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        shifters_list = ShifterApplicant.objects.filter(department=info.departmentID.courseName)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            shifters_list = shifters_list.filter(Q(lname__icontains=searchthis_query) | Q(studentID__icontains=searchthis_query)| Q(fname__icontains=searchthis_query)| Q(mname__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = {
        'info' : info,
        'shifters_list' : shifters_list,
        }
        return render (request, 'chairperson/Others/cOthers-shifter.html', context)

def shifter_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        shifters_masterlist =ShifterApplicant.objects.filter(department=info.departmentID.courseName)
        shifters_returned = ShifterApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Returned")
        shifters_submitted = ShifterApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Submitted")
        shifters_forwared = ShifterApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Forwarded")
        shifters_inprogress = ShifterApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="In Progress")
        shifters_complete = ShifterApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'shifters_masterlist': shifters_masterlist,
        'shifters_submitted' : shifters_submitted,
        'shifters_returned' : shifters_returned,
        'shifters_forwarded' : shifters_forwared,
        'shifters_inprogress' : shifters_inprogress,
        'shifters_complete' : shifters_complete,
        
        }
        return render (request, 'chairperson/Others/cOthers-shifter-Master.html', context)

#VIEW REQUEST OF SHIFTERS
def shifter_view(request, shift_id):
    if request.method == 'GET':
        shift = ShifterApplicant.objects.get(pk=shift_id)
        return render(request, 'chairperson/Others/cOthers-shifterView.html', {'shift': shift,})
    elif request.method == 'POST':
        shift = ShifterApplicant.objects.get(pk=shift_id)
        statform = request.POST.get('slct')
        shift.remarks = statform
        shift.save()
        return redirect ('cOthers-shifter')

# FOR SHIFTER FEEDBACK        
def shifter_feedback(request, shift_id):
    if request.method == 'GET':
        shift_feedback = ShifterApplicant.objects.get(pk=shift_id)
        return render (request, 'chairperson/Others/cOthers-shifter-feedback.html', {'shift_feedback' : shift_feedback})
    elif request.method == 'POST':
        comms = ShifterApplicant.objects.get(pk=shift_id)
        comm = request.POST.get('actionRequired')
        comms.shifter_comment= comm
        comms.save()
        messages.success(request, 'Feedback Succesfully Sent!')
        return HttpResponseRedirect(reverse('cOthers-shifter-feedback', args=(shift_id,)))


#SHIFTERS CSW 
def shifter_csw(request, shift_id):
    shift_csw = ShifterApplicant.objects.get(pk=shift_id)
    if shift_csw.department== 'BSIT':
        return render (request, 'chairperson/Others/cOthers-shifter-itcsw.html', {'shift_csw' : shift_csw})
    elif shift_csw.department == 'BSEE':
        return render (request, 'chairperson/Others/cOthers-shifter-eecsw.html', {'shift_csw' : shift_csw})

#SHIFTER CSW TO PDF
def shifter_Pdf(request, shift_id):
    try:
        pdf1 = ShifterApplicant.objects.get(pk=shift_id)
        if pdf1.department == 'BSIT':
            data = request.session.get('_shifter_data')

            template = get_template('chairperson/CSW/it_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['actionRequired'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/it_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "IT_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")

        elif pdf1.department == 'BSEE':
            data = request.session.get('_shifter_data')

            template = get_template('chairperson/CSW/ee_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['actionRequired'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/ee_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "EE_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")
    except:
        return HttpResponse("Not found please attach first")

# FOR DELETING SHIFTER FILES
def del_allshifter(request, shift_id):
    shift_applicant = ShifterApplicant.objects.get(pk=shift_id)
    shift_applicant.studentStudyplan.delete()
    shift_applicant.studentshifterletter.delete()
    shift_applicant.studentGrade.delete()
    messages.success(request, 'Files Succesfully Returned!')  
    return HttpResponseRedirect(reverse('cOthers-shifterView', args=(shift_id,)))

# FOR VIEWING TRANSFEREE LIST
def transferee_list(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        trans_list = TransfereeApplicant.objects.filter(department=info.departmentID.courseName)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            trans_list = trans_list.filter(Q(lname__icontains=searchthis_query) | Q(studentID__icontains=searchthis_query)| Q(fname__icontains=searchthis_query)| Q(mname__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
        context = { 'trans_list' : trans_list,
        'info' : info,
        }
        return render (request, 'chairperson/Others/cOthers-transferee.html', context) 

def transferee_masterlist(request):
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        trans_masterlist =TransfereeApplicant.objects.filter(department=info.departmentID.courseName)
        trans_returned = TransfereeApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Returned")
        trans_submitted = TransfereeApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Submitted")
        trans_forwared = TransfereeApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Forwarded")
        trans_inprogress = TransfereeApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="In Progress")
        trans_complete = TransfereeApplicant.objects.filter(department=info.departmentID.courseName).filter(remarks="Complete")
       
        context = {
        'info' : info,
        'trans_masterlist':trans_masterlist,
        'trans_submitted' : trans_submitted,
        'trans_returned' : trans_returned,
        'trans_forwarded' : trans_forwared,
        'trans_inprogress' : trans_inprogress,
        'trans_complete' : trans_complete,
        
        }
        return render (request, 'chairperson/Others/cOthers-transferee-Master.html', context)

# VIEWING REQUEST OF TRANSFEREE
def transferee_view(request, transf_id):
    if request.method == 'GET':
        trans = TransfereeApplicant.objects.get(pk=transf_id)
        return render(request, 'chairperson/Others/cOthers-transfereeView.html', {'trans' : trans})
    elif request.method == 'POST':
        trans = TransfereeApplicant.objects.get(pk=transf_id)
        statform = request.POST.get('slct')
        trans.remarks = statform
        trans.save()  
        return redirect ('cOthers-transferee')


# FOR SHIFTER FEEDBACK        
def transferee_feedback(request, transf_id):
    if request.method == 'GET':
        transf_feedback = TransfereeApplicant.objects.get(pk=transf_id)
        return render (request, 'chairperson/Others/cOthers-transferee-feedback.html', {'transf_feedback' : transf_feedback})
    elif request.method == 'POST':
        comms = TransfereeApplicant.objects.get(pk=transf_id)
        comm = request.POST.get('actionRequired')
        comms.transfer_comment= comm
        comms.save()
        messages.success(request, 'Feedback Succesfully Sent!')
        return HttpResponseRedirect(reverse('cOthers-transferee-feedback', args=(transf_id,)))

#TRANSFEREE CSW
def transferee_csw(request, transf_id):
    trans_csw = TransfereeApplicant.objects.get(pk=transf_id)
    if trans_csw.department == 'BSIT':
        return render (request, 'chairperson/Others/cOthers-transferee-itcsw.html', {'trans_csw' : trans_csw})
    elif trans_csw.department == 'BSEE':
        return render (request, 'chairperson/Others/cOthers-transferee-eecsw.html', {'trans_csw' : trans_csw})   

#TRANSFEREE CSW TO PDF
def transferee_Pdf(request, transf_id):
    try:
        pdf1 = TransfereeApplicant.objects.get(pk=transf_id)
        if pdf1.department == 'BSIT':
            data = request.session.get('_transfer_data')

            template = get_template('chairperson/CSW/it_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['actionRequired'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/it_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "IT_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")

        elif pdf1.studentID.departmentID.courseName == 'BSEE':
            data = request.session.get('_transfer_data')

            template = get_template('chairperson/CSW/ee_csw.html')

            context =  {'pdf1':pdf1,'date':data['date'],'from':data['from'],'subject':data['subject'],'action':data['actionRequired'],'reference':data['reference'],'background':data['background'],'analysis':data['analysis'],'recommendation':data['recommendation'], }
                
            html = template.render(context)
            pdf = render_to_pdf('chairperson/CSW/ee_csw.html', context)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "EE_CSW-%s.pdf" %pdf1.studentID
                content = "inline; filename=%s" %(filename)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename='%s'" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")
    except:
        return HttpResponse("Not found please attach first")

# FOR DELETING TRANSFEREE FILES
def del_alltransferee(request, transf_id):
    transf_applicant = TransfereeApplicant.objects.get(pk=transf_id)
    transf_applicant.studentStudyplan.delete()
    transf_applicant.studentNote.delete()
    transf_applicant.studentHD.delete()
    transf_applicant.studentGoodmoral.delete()
    transf_applicant.studentGrade.delete()
    messages.success(request, 'Succesfully DELETED!')  
    return HttpResponseRedirect(reverse('cOthers-transfereeView', args=(transf_id,)))


#FOR SENDING EMAIL
def sendmailwfile(request, email_id):
    if request.method == 'POST':
        if request.POST.get("loa-email"):
            sends = LOAApplicant.objects.get(pk=email_id)
            message='Here are the details attached'  # ibahin niyo na lang yung message, subject, pati mail_id
            subject=''                # pati mail_id1
            mail_id = sends.studentID.studentUser.email  #paki palitan na lang ng email ng signatories
            mail_id1 = 'cperson.dummy@gmail.com'
            email=EmailMessage(subject,message,EMAIL_HOST_USER,[mail_id],[mail_id1])
            email.content_subtype='html'

            try:
                cswfile = request.FILES['uploadCSW']
            except MultiValueDictKeyError:
                messages.error(request, 'Please UPLOAD CSW file first')
                return HttpResponseRedirect(reverse('cOthers-loaView', args=(email_id,)))

            try:
                email.attach(cswfile.name, cswfile.read(), cswfile.content_type)
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentLOAClearanceform.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentStudyplan.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentLOAletter.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentLOAFORM.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentChecklist.name))
                email.send()
                messages.success(request, 'Message Sent Succesfully!')
                return HttpResponseRedirect(reverse('cOthers-loaView', args=(email_id,)))
            except PermissionError:  
                messages.error(request, 'Files to be send, is not complete yet')
                return HttpResponseRedirect(reverse('cOthers-loaView', args=(email_id,)))
        
        elif request.POST.get("shifter-email"):
            sends = ShifterApplicant.objects.get(pk=email_id)
            message='Here are the details attached'  # ibahin niyo na lang yung message, subject, pati mail_id
            subject=''                # pati mail_id1
            mail_id = sends.eadd  #paki palitan na lang ng email ng signatories
            mail_id1 = 'cperson.dummy@gmail.com'
            email=EmailMessage(subject,message,EMAIL_HOST_USER,[mail_id],[mail_id1])
            email.content_subtype='html'

            try:
                cswfile = request.FILES['uploadCSW']
            except MultiValueDictKeyError:
                messages.error(request, 'Please UPLOAD CSW file first')
                return HttpResponseRedirect(reverse('cOthers-shifterView', args=(email_id,)))

            try:
                email.attach(cswfile.name, cswfile.read(), cswfile.content_type)
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentStudyplan.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentshifterletter.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentGrade.name))
                email.send()
                messages.success(request, 'Message Sent Succesfully!')
                return HttpResponseRedirect(reverse('cOthers-shifterView', args=(email_id,)))
            except PermissionError:  
                messages.error(request, 'Files to be send, is not complete yet')
                return HttpResponseRedirect(reverse('cOthers-shifterView', args=(email_id,)))

        elif request.POST.get("transfer-email"):
            sends = TransfereeApplicant.objects.get(pk=email_id)
            message='Here are the details attached'  # ibahin niyo na lang yung message, subject, pati mail_id
            subject=''                # pati mail_id1
            mail_id = sends.eadd     #paki palitan na lang ng email ng signatories
            mail_id1 = 'cperson.dummy@gmail.com'  
            email=EmailMessage(subject,message,EMAIL_HOST_USER,[mail_id],[mail_id1])
            email.content_subtype='html'

            try:
                cswfile = request.FILES['uploadCSW']
            except MultiValueDictKeyError:
                messages.error(request, 'Please UPLOAD CSW file first')
                return HttpResponseRedirect(reverse('cOthers-transfereeView', args=(email_id)))

            try:
                email.attach(cswfile.name, cswfile.read(), cswfile.content_type)
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentStudyplan.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentNote.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentGoodmoral.name))
                email.attach_file(os.path.join(settings.MEDIA_ROOT,sends.studentHD.name))
                email.send()
                messages.success(request, 'Message Sent Succesfully!')
                return HttpResponseRedirect(reverse('cOthers-transfereeView', args=(email_id,)))
            except PermissionError:  
                messages.error(request, 'Files to be send, is not complete yet')
                return HttpResponseRedirect(reverse('cOthers-transfereeView', args=(email_id,)))

#SCHEDULING BY BLOCK
def viewblock(request):
        return render (request, 'chairperson/Stud_sched/cStudentViewBlock.html')

def schedOnline(request):
    id= request.user.id
    info = FacultyInfo.objects.get(facultyUser=id)
    if info.departmentID.courseName == 'BSIT':
        blocks1 = BlockSection.objects.filter(blockCourse="BSIT").filter(blockYear="1")
        blocks2 = BlockSection.objects.filter(blockCourse="BSIT").filter(blockYear="2")
        blocks3 = BlockSection.objects.filter(blockCourse="BSIT").filter(blockYear="3")
        blocks4 = BlockSection.objects.filter(blockCourse="BSIT").filter(blockYear="4")
    else:
        blocks1 = BlockSection.objects.filter(blockCourse="BSEE", blockYear="1")
        blocks2 = BlockSection.objects.filter(blockCourse="BSEE", blockYear="2")
        blocks3 = BlockSection.objects.filter(blockCourse="BSEE", blockYear="3")
        blocks4 = BlockSection.objects.filter(blockCourse="BSEE", blockYear="4")
    return render (request, 'chairperson/Stud_sched/cStudentSchedOnline.html', {"blocks1": blocks1 , "blocks2": blocks2,"blocks3": blocks3,"blocks4": blocks4})


def schedOnline2(request,block_id):  
    id= request.user.id
    acads = AcademicYearInfo.objects.get(pk=1)
    info = FacultyInfo.objects.get(facultyUser=id)
    schedule = studentScheduling.objects.filter(realsection=block_id)
    OrderFormSet = inlineformset_factory(BlockSection, studentScheduling, fields=('subjectCode','instructor', 'section','day','timeStart','timeEnd', 'room', 'type'),widgets={'subjectCode': forms.Select(attrs={"class": "form-control", "id":"instructorField", "required":True}), 'instructor': forms.Select(attrs={"class": "form-control", "id":"instructorField"}),'section': forms.NumberInput(attrs={"class": "form-control", "placeholder": "Section", "id":"instructorField", "required":True}),'day': forms.Select(attrs={"class": "form-control", "id":"remarks", "required":True}),'timeStart': forms.TimeInput(attrs={"class": "form-control", "placeholder": "%H:%M:%S", "id":"timeField", "required":True}),'timeEnd': forms.TimeInput(attrs={"class": "form-control","placeholder": "%H:%M:%S", "id":"timeField", "required":True}),'room': forms.Select(attrs={"class": "form-control", "placeholder": "Room", "id":"instructorField", "required":True}),'type': forms.Select(attrs={"class": "form-control", "id":"instructorField", "required":True})}, max_num=1, can_delete=False)
    block1 = BlockSection.objects.get(id=block_id)
    formset = OrderFormSet(queryset=studentScheduling.objects.none(), instance=block1)
    for form in formset:
        form.fields['subjectCode'].queryset = curriculumInfo.objects.filter(curriculumyear=block1.curryear).filter(departmentID=info.departmentID).filter(schoolYear=block1.blockYear).filter(schoolSem=acads.semester)
       
    if request.method =='POST':
        formset = OrderFormSet(request.POST, instance=block1)

        if formset.is_valid():
            global flag
            flag = 0
            for form in formset:
                data=form.cleaned_data
                block = str(block1)

            #THIS BLOCK IS FOR COMMON TIME INPUT ERROR

            tsinput = str(data.get('timeStart')).split(':')
            teinput = str(data.get('timeEnd')).split(':')
            if float(tsinput[0]) < 7:
                messages.error(request, 'Time input must not be less than 7:00')
                print("TIME ERROR EARLY MET")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif (float(teinput[0])+(float(teinput[1])/60)) > 22:
                messages.error(request, 'Time input must be no more than 22:00')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            elif float(tsinput[0]+tsinput[1])>=float(teinput[0]+teinput[1]):
                messages.error(request, 'Time Start must not equal or be later than Time End')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                pass

            if studentScheduling.objects.all().exists():
                sched = studentScheduling.objects.all()
                for a in sched:      
                    blockcur = a.realsection
                    blockcurs=str(blockcur)
                    if block == blockcurs:
                        startDb=a.timeStart
                        endDb=a.timeEnd
                        dayDb=a.day
                        dayinp=data.get('day')
                        subinp = data.get('subjectCode')
                        subDb = a.subjectCode
                        if dayinp == dayDb: 
                            flag = 0
                            startinp = data.get('timeStart')
                            endinp = data.get('timeEnd')
                        
                            sdb=str(startDb)
                            edb=str(endDb)
                            sinp=str(startinp)
                            einp=str(endinp)

                            #splitting the strings
                            sdb2 = sdb.split(":")
                            edb2 = edb.split(":")
                            sinp2 = sinp.split(":")
                            einp2 = einp.split(":")

                            #convert into integer
                            sh=(sdb2[0])
                            sm=(sdb2[1])
                            eh=(edb2[0])
                            em=(edb2[1])


                            sh2=(sinp2[0])
                            sm2=(sinp2[1])
                            eh2=(einp2[0])
                            em2=(einp2[1])

                            intsh = int(sh)
                            intsm = int(sm)
                            inteh = int(eh)
                            intem = int(em)

                            intsh2 = int(sh2)
                            intsm2 = int(sm2)
                            inteh2 = int(eh2)
                            intem2 = int(em2)

                            if intsh2 < intsh: #Start Hour Input is Earlier than in Start Hur database
                                if inteh2 <= intsh: #End Hour input is equal or earlier than start Hour
                                    if intem2 <= intsm: #End Minutes input is earlier than Start Minutes in Database 
                                        flag = 1 #Valid Schedule
                                    else:
                                        break #Invalid Schedule end minutes has conflict with start minutes in database
                                else:
                                    break #Invalid Schedule end Hour input conflict with start hour in database

                            elif intsh2 > intsh: #Start Hour Input is later than database hour
                                if intsh2 >= inteh: # If Start Hour is later or equal to end hour in database
                                    if intsm2 >= intem: #If Minute Input is Later than or equal end Min in database
                                        flag=1 #Valid Sched
                                    else:
                                        break # Conflict With Minutes
                                else:
                                    break #Conflict with Hour
                                    

                            elif intsh2 == intsh: #If start Hour Input is equal to start Hour in database 
                                if intsm2 < intsm: #If start Min input is earlier than start min in database
                                    if inteh2 <= intsh: #If end hour input is earlier or equal to start hour database
                                        if intem2 <= intsm: #If end minutes is earlier or equal to start min database 
                                            flag=1 #Valid Sched
                                        else:
                                            break # Conflict in Minutes
                                    else:
                                        break#conflict in Hour 
                                else:
                                    break#Conflict in starting minute time is later than minutes

                            else:
                                continue#time does not fall in any category time of conflict
                        else:
                            continue#day is not the same in database
                    else:
                        continue#section is not the same as database compared

                flag3 = 0
                catcher = 0
                for a in sched:
                    blockcur = a.realsection
                    blockcurs=str(blockcur)
                    if block == blockcurs:
                        dayinps=data.get('day')
                        dayDbs=a.day
                        subinps = data.get('subjectCode')
                        subDbs = a.subjectCode
                        if subinps == subDbs:
                            typeinps = data.get('type')
                            typeDb = a.type
                            if typeinps != typeDb:
                                if dayinps == dayDbs:
                                    flag3=flag3+1
                                    if flag > 0:
                                        #JM CODE
                                        print("FLAG = 1, study plan dapat masave pero di dahil sa prof")
                                        faculty_Schedule = studentScheduling.objects.all()
                                        for DATA in formset:
                                            inputtedData = DATA.cleaned_data
                                        validProf = False

                                        #This Code is for Faculty Availability Checking

                                        try:
                                            profInfo = FacultyInfo.objects.get(facultyUser = inputtedData.instructor)  
                                            profAvailIn = str(profInfo.facultyIn).split(':')
                                            profAvailOut = str(profInfo.facultyOut).split(':')
                                            FacAvailTimeIn = float(profAvailIn[0])+float(float(profAvailIn[1])/60)
                                            FacAvailTimeOut = float(profAvailOut[0])+float(float(profAvailOut[1])/60)

                                            print("IN Get:",inTimeSubj,"Avail:", FacAvailTimeIn)
                                            print("Out Get:",outTimeSubj,"Avail:", FacAvailTimeOut)
                                            
                                            testTimeInput = (str(inputtedData.timeStart)).split(":")  
                                            testTimeOutput = (str(inputtedData.timeEnd)).split(":")

                                            TimeTestIn = float(testTimeInput[0])+float(float(testTimeInput[1])/60) 
                                            TimeTestOut = float(testTimeOutput[0])+float(float(testTimeOutput[1])/60)  


                                            if float(TimeTestIn) < float(FacAvailTimeIn):
                                                #Input Start Time To Early too Availability
                                                validProf = False
                                                errorMessage = "Faculty Time In: " + str(profAvailIn[0]) +":" + str(profAvailIn[1])+", too early"
                                            elif float(TimeTestOut) > float(FacAvailTimeOut):
                                                validProf = False
                                                errorMessage = "Faculty Time Out" + str(profAvailOut[0]) +":" + str(profAvailOut[1])+ ", too late"
                                            else:
                                                validProf = True
                                        except:
                                            validProf = True


                                        #This Code is for Assigned Sched Prof in database if there are  overlaps 

                                        for databaseInfo in faculty_Schedule:
                                            dbSubject = databaseInfo.subjectCode
                                            dbSection = databaseInfo.section
                                            dbProf = databaseInfo.instructor
                                            dbDay = databaseInfo.day
                                            dbTimeIn = str(databaseInfo.timeStart)
                                            dbInTime = dbTimeIn.split(":")
                                            dbHourIn = float(dbInTime[0])
                                            dbMinIn = float(dbInTime[1])/60
                                            dbStartTime = dbHourIn + dbMinIn
                                            stringinputTimeStart = str(inputtedData.get('timeStart'))
                                            list_of_timeStarted = stringinputTimeStart.split(":")
                                            inputStartTime = float(list_of_timeStarted[0])+float(float(list_of_timeStarted[1])/60)
                                            dbTimeOut = str(databaseInfo.timeEnd)
                                            dbOutTime = dbTimeOut.split(":")
                                            dbHourOut = float(dbOutTime[0])
                                            dbMinOut = float(dbOutTime[1])/60
                                            dbEndTime = dbHourOut + dbMinOut
                                            stringinputTimeEnd = str(inputtedData.get('timeEnd'))
                                            list_of_timeEnded = stringinputTimeEnd.split(":")
                                            inputEndTime = float(list_of_timeEnded[0])+float(float(list_of_timeEnded[1])/60)

                                            prof_assigned = inputtedData.get('instructor')
                                            if prof_assigned == dbProf:
                                                print(validProf)
                                                if dbDay == inputtedData.get('day'):
                                                    if inputStartTime == dbStartTime:
                                                        #Same Day and Start Time Sched
                                                        subjCode = str(dbSubject).split("|")
                                                        print(subjCode)
                                                        errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Same Start Time"
                                                        validProf = False
                                                        break
                                                    else:
                                                        if inputStartTime >= dbEndTime:
                                                            #After the Given Schedule
                                                            validProf = True
                                                        else:
                                                            #Start time earlier than stored end time
                                                            if inputEndTime <= dbStartTime:
                                                                # Sched is Confirmed Earlier than given sched
                                                                validProf = True
                                                            else:
                                                                # End time overlap with start time
                                                                subjCode = str(dbSubject).split("|")
                                                                print(subjCode)
                                                                errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Time Overlap"
                                                                validProf = False
                                                                break
                                                else:
                                                    validProf = True
                                            else:
                                                validProf = True       
                                            
                                        print("dbProf:", dbProf," prof_assigned:",prof_assigned)
                                        print("inputValue:",inputStartTime,"-",inputEndTime)
                                        print("testValue:", dbStartTime,"-",dbEndTime)
                                        print(validProf,"flag:", flag,"flag3:", flag3)
                                        #JM CODE
                                        if inputtedData.get('instructor') is None:
                                            print("IT GOES HERE")
                                            validProf = True

                                        roomVacancy = data.get('room')
                                        roomDB = studentScheduling.objects.all()
                                        validRoom = True
                                        for i in roomDB:
                                            if roomVacancy.room == i.room:
                                                roomDay = i.day
                                                roomStart = str(i.timeStart)
                                                roomEnd = str(i.timeEnd)

                                                roomStartList = roomStart.split(":")
                                                roomEndList = roomEnd.split(":")

                                                roomStartTime = float(roomStartList[0])+float(float(roomStartList[1])/60)
                                                roomEndTime = float(roomEndList[0])+float(float(roomEndList[1])/60)

                                                if inputtedData.get('day') == roomDay:
                                                    #CODE FOR TIME BLOCKING
                                                    if inputStartTime == roomStartTime:
                                                        #Sched in room Already Existed
                                                        subjCode = str(i.subjectCode).split("|")
                                                        print(subjCode)
                                                        errorMessage = subjCode[2] +" in " + str(i.realsection) + " Same Start Time"
                                                        validRoom = False
                                                        
                                                        break
                                                    else:
                                                        #room sched are not the same
                                                        if inputStartTime >= roomEndTime:
                                                            #Input Sched is After the sched in Database
                                                            validRoom = True
                                                        else:
                                                            #Input Sched is not after the Sched in Database
                                                            if inputEndTime <= roomStartTime:
                                                                #Input Sched is earlier than Sched in Databse
                                                                validRoom = True
                                                            else:
                                                                #Input Sched Conflict in DB Sched
                                                                subjCode = str(i.subjectCode).split("|")
                                                                print(subjCode)
                                                                errorMessage = str(subjCode[2]) +" in " +str( i.realsection) + " Time Conflct"
                                                                validRoom = False
                                                                break 
                                                else:
                                                    #No Day Exist in the room 
                                                    validRoom = True
                                        else:
                                            if studentScheduling.objects.filter(room = roomVacancy).count() == 0:
                                                validRoom = True

                                        limitless_rooms = ["NA", "N.A.", "N/A", "T.B.A.", "TBA", "MS TEAMS", "FIELD","MS Teams","Ms Teams","Field","GYM","Gym"]
                                        print(limitless_rooms," in ", roomVacancy)
                                        if roomVacancy.room in limitless_rooms:
                                            validRoom = True  

                                        if validProf == True:
                                            if validRoom == True:
                                                formset.save()
                                                validProf = False
                                                validRoom = False
                                                messages.success(request, 'Schedule successfully Added!')
                                                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                            else:
                                                messages.error(request, 'Room and Time error: %s' % errorMessage)
                                                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                                        else:
                                            messages.error(request, 'Faculty Time Error: %s' %errorMessage)
                                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                                    else:
                                        messages.error(request, 'Time already taken')
                                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                        #messages.error(request, 'Time already taken')
                            else:
                                messages.error(request, 'Subject already taken')
                                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                #messages.error(request, 'Time already taken')
                        elif dayinps == dayDbs:
                            flag3=flag3+1
                            if flag > 0:
                                #NEW
                                #JM CODE
                                print("FLAG = 1, study plan dapat masave pero di dahil sa prof")
                                faculty_Schedule = studentScheduling.objects.all()
                                for DATA in formset:
                                    inputtedData = DATA.cleaned_data
                                validProf = False

                                #This Code is for Faculty Availability Checking

                                try:
                                    profInfo = FacultyInfo.objects.get(facultyUser = inputtedData.instructor)  
                                    profAvailIn = str(profInfo.facultyIn).split(':')
                                    profAvailOut = str(profInfo.facultyOut).split(':')
                                    FacAvailTimeIn = float(profAvailIn[0])+float(float(profAvailIn[1])/60)
                                    FacAvailTimeOut = float(profAvailOut[0])+float(float(profAvailOut[1])/60)

                                    print("IN Get:",inTimeSubj,"Avail:", FacAvailTimeIn)
                                    print("Out Get:",outTimeSubj,"Avail:", FacAvailTimeOut)
                                    
                                    testTimeInput = (str(inputtedData.timeStart)).split(":")  
                                    testTimeOutput = (str(inputtedData.timeEnd)).split(":")

                                    TimeTestIn = float(testTimeInput[0])+float(float(testTimeInput[1])/60) 
                                    TimeTestOut = float(testTimeOutput[0])+float(float(testTimeOutput[1])/60)  


                                    if float(TimeTestIn) < float(FacAvailTimeIn):
                                        #Input Start Time To Early too Availability
                                        validProf = False
                                        errorMessage = "Faculty Time In: " + str(profAvailIn[0]) +":" + str(profAvailIn[1])+", too early"
                                    elif float(TimeTestOut) > float(FacAvailTimeOut):
                                        validProf = False
                                        errorMessage = "Faculty Time Out" + str(profAvailOut[0]) +":" + str(profAvailOut[1])+ ", too late"
                                    else:
                                        validProf = True
                                except:
                                    validProf = True


                                #This Code is for Assigned Sched Prof in database if there are  overlaps 

                                for databaseInfo in faculty_Schedule:
                                    dbSubject = databaseInfo.subjectCode
                                    dbSection = databaseInfo.section
                                    dbProf = databaseInfo.instructor
                                    dbDay = databaseInfo.day
                                    dbTimeIn = str(databaseInfo.timeStart)
                                    dbInTime = dbTimeIn.split(":")
                                    dbHourIn = float(dbInTime[0])
                                    dbMinIn = float(dbInTime[1])/60
                                    dbStartTime = dbHourIn + dbMinIn
                                    stringinputTimeStart = str(inputtedData.get('timeStart'))
                                    list_of_timeStarted = stringinputTimeStart.split(":")
                                    inputStartTime = float(list_of_timeStarted[0])+float(float(list_of_timeStarted[1])/60)
                                    dbTimeOut = str(databaseInfo.timeEnd)
                                    dbOutTime = dbTimeOut.split(":")
                                    dbHourOut = float(dbOutTime[0])
                                    dbMinOut = float(dbOutTime[1])/60
                                    dbEndTime = dbHourOut + dbMinOut
                                    stringinputTimeEnd = str(inputtedData.get('timeEnd'))
                                    list_of_timeEnded = stringinputTimeEnd.split(":")
                                    inputEndTime = float(list_of_timeEnded[0])+float(float(list_of_timeEnded[1])/60)

                                    prof_assigned = inputtedData.get('instructor')
                                    if prof_assigned == dbProf:
                                        print(validProf)
                                        if dbDay == inputtedData.get('day'):
                                            if inputStartTime == dbStartTime:
                                                #Same Day and Start Time Sched
                                                subjCode = str(dbSubject).split("|")
                                                print(subjCode)
                                                errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Same Start Time"
                                                validProf = False
                                                break
                                            else:
                                                if inputStartTime >= dbEndTime:
                                                    #After the Given Schedule
                                                    validProf = True
                                                else:
                                                    #Start time earlier than stored end time
                                                    if inputEndTime <= dbStartTime:
                                                        # Sched is Confirmed Earlier than given sched
                                                        validProf = True
                                                    else:
                                                        # End time overlap with start time
                                                        subjCode = str(dbSubject).split("|")
                                                        print(subjCode)
                                                        errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Time Overlap"
                                                        validProf = False
                                                        break
                                        else:
                                            validProf = True
                                    else:
                                        validProf = True       
                                    
                                print("dbProf:", dbProf," prof_assigned:",prof_assigned)
                                print("inputValue:",inputStartTime,"-",inputEndTime)
                                print("testValue:", dbStartTime,"-",dbEndTime)
                                print(validProf,"flag:", flag,"flag3:", flag3)
                                #JM CODE
                                if inputtedData.get('instructor') is None:
                                    print("IT GOES HERE")
                                    validProf = True

                                roomVacancy = data.get('room')
                                roomDB = studentScheduling.objects.all()
                                validRoom = True
                                for i in roomDB:
                                    if roomVacancy.room == i.room.room:
                                        roomDay = i.day
                                        roomStart = str(i.timeStart)
                                        roomEnd = str(i.timeEnd)

                                        roomStartList = roomStart.split(":")
                                        roomEndList = roomEnd.split(":")

                                        roomStartTime = float(roomStartList[0])+float(float(roomStartList[1])/60)
                                        roomEndTime = float(roomEndList[0])+float(float(roomEndList[1])/60)

                                        if inputtedData.get('day') == roomDay:
                                            #CODE FOR TIME BLOCKING
                                            if inputStartTime == roomStartTime:
                                                #Sched in room Already Existed
                                                subjCode = str(i.subjectCode).split("|")
                                                print(subjCode)
                                                errorMessage = subjCode[2] +" in " + str(i.realsection) + " Same Start Time"
                                                validRoom = False
                                                
                                                break
                                            else:
                                                #room sched are not the same
                                                if inputStartTime >= roomEndTime:
                                                    #Input Sched is After the sched in Database
                                                    validRoom = True
                                                else:
                                                    #Input Sched is not after the Sched in Database
                                                    if inputEndTime <= roomStartTime:
                                                        #Input Sched is earlier than Sched in Databse
                                                        validRoom = True
                                                    else:
                                                        #Input Sched Conflict in DB Sched
                                                        subjCode = str(i.subjectCode).split("|")
                                                        print(subjCode)
                                                        errorMessage = str(subjCode[2]) +" in " +str( i.realsection) + " Time Conflct"
                                                        validRoom = False
                                                        break 
                                        else:
                                            #No Day Exist in the room 
                                            validRoom = True
                                else:
                                    if studentScheduling.objects.filter(room = roomVacancy).count() == 0:
                                        validRoom = True

                                limitless_rooms = ["NA", "N.A.", "N/A", "T.B.A.", "TBA", "MS TEAMS", "FIELD","Ms Teams","Field","GYM","Gym","MS Teams"]
                                print(limitless_rooms," in ", roomVacancy)
                                if roomVacancy.room in limitless_rooms:
                                    validRoom = True  

                                if validProf == True:
                                    if validRoom == True:
                                        formset.save()
                                        validProf = False
                                        validRoom = False
                                        messages.success(request, 'Schedule successfully Added!')
                                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                    else:
                                        messages.error(request, 'Room and Time error: %s' % errorMessage)
                                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                                else:
                                    messages.error(request, 'Faculty Time Error: %s' %errorMessage)
                                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                #NEW
                            else:
                                messages.error(request, 'Time already taken')
                                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                                #messages.error(request, 'Time already taken')
                    else:
                        continue     
                if flag3 == 0:
                    #JM CODE
                    print("FLAG3 = 0, study plan dapat masave pero di dahil sa prof")
                    faculty_Schedule = studentScheduling.objects.all()
                    for DATA in formset:
                        inputtedData = DATA.cleaned_data
                    validProf = False

                    #This Code is for Faculty Availability Checking

                    try:
                        profInfo = FacultyInfo.objects.get(facultyUser = inputtedData.instructor)  
                        profAvailIn = str(profInfo.facultyIn).split(':')
                        profAvailOut = str(profInfo.facultyOut).split(':')
                        FacAvailTimeIn = float(profAvailIn[0])+float(float(profAvailIn[1])/60)
                        FacAvailTimeOut = float(profAvailOut[0])+float(float(profAvailOut[1])/60)

                        print("IN Get:",inTimeSubj,"Avail:", FacAvailTimeIn)
                        print("Out Get:",outTimeSubj,"Avail:", FacAvailTimeOut)
                        
                        testTimeInput = (str(inputtedData.timeStart)).split(":")  
                        testTimeOutput = (str(inputtedData.timeEnd)).split(":")

                        TimeTestIn = float(testTimeInput[0])+float(float(testTimeInput[1])/60) 
                        TimeTestOut = float(testTimeOutput[0])+float(float(testTimeOutput[1])/60)  


                        if float(TimeTestIn) < float(FacAvailTimeIn):
                            #Input Start Time To Early too Availability
                            validProf = False
                            errorMessage = "Faculty Time In: " + profAvailIn[0] +":" + profAvailIn[1]+", too early"
                        elif float(TimeTestOut) > float(FacAvailTimeOut):
                            validProf = False
                            errorMessage = "Faculty Time Out" + profAvailOut[0] +":" + profAvailOut[1]+ ", too late"
                        else:
                            validProf = True
                    except:
                        validProf = True

                    for databaseInfo in faculty_Schedule:
                        dbSubject = databaseInfo.subjectCode
                        dbSection = databaseInfo.section
                        dbProf = databaseInfo.instructor
                        dbDay = databaseInfo.day
                        dbTimeIn = str(databaseInfo.timeStart)
                        dbInTime = dbTimeIn.split(":")
                        dbHourIn = float(dbInTime[0])
                        dbMinIn = float(dbInTime[1])/60
                        dbStartTime = dbHourIn + dbMinIn
                        stringinputTimeStart = str(inputtedData.get('timeStart'))
                        list_of_timeStarted = stringinputTimeStart.split(":")
                        inputStartTime = float(list_of_timeStarted[0])+float(float(list_of_timeStarted[1])/60)
                        dbTimeOut = str(databaseInfo.timeEnd)
                        dbOutTime = dbTimeOut.split(":")
                        dbHourOut = float(dbOutTime[0])
                        dbMinOut = float(dbOutTime[1])/60
                        dbEndTime = dbHourOut + dbMinOut
                        stringinputTimeEnd = str(inputtedData.get('timeEnd'))
                        list_of_timeEnded = stringinputTimeEnd.split(":")
                        inputEndTime = float(list_of_timeEnded[0])+float(float(list_of_timeEnded[1])/60)
                        prof_assigned = inputtedData.get('instructor')
                        print(prof_assigned)
                        #If Time Availibility Test Passes
                        if prof_assigned == dbProf:
                            print(validProf)
                            if dbDay == inputtedData.get('day'):
                                if inputStartTime == dbStartTime:
                                    #Same Day and Start Time Sched
                                    subjCode = str(dbSubject).split("|")
                                    print(subjCode)
                                    errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Time Overlap"
                                    validProf = False
                                    break
                                else:
                                    if inputStartTime >= dbEndTime:
                                        validProf = True
                                    else:
                                        #Start time earlier than stored end time
                                        if inputEndTime <= dbStartTime:
                                            # Sched is Confirmed Earlier than given sched
                                            validProf = True
                                        else:
                                            # End time overlap with start time
                                            validProf = False
                                            subjCode = str(dbSubject).split("|")
                                            print(subjCode)
                                            errorMessage = str(subjCode[2]) + " in " + str(databaseInfo.realsection) + " Time Overlap"
                                            break
                            else:
                                validProf = True
                        else:
                            validProf = True
                               

                    print("dbProf:", dbProf," prof_assigned:",prof_assigned)
                    print("inputValue:",inputStartTime,"-",inputEndTime)
                    print("testValue:", dbStartTime,"-",dbEndTime)
                
                    if inputtedData.get('instructor') is None:
                        print("IT GOES HERE")
                        validProf = True

                    roomVacancy = data.get('room')
                    roomDB = studentScheduling.objects.filter(room = roomVacancy)
                    validRoom = True
                    for i in roomDB:
                        if roomVacancy.room == i.room.room:
                            roomDay = i.day
                            roomStart = str(i.timeStart)
                            roomEnd = str(i.timeEnd)
                            roomStartList = roomStart.split(":")
                            roomEndList = roomEnd.split(":")
                            roomStartTime = float(roomStartList[0])+float(float(roomStartList[1])/60)
                            roomEndTime = float(roomEndList[0])+float(float(roomEndList[1])/60)

                            if inputtedData.get('day') == roomDay:
                                #CODE FOR TIME BLOCKING
                                if inputStartTime == roomStartTime:
                                    #Sched in room Already Existed
                                        subjCode = str(i.subjectCode).split("|")
                                        print(subjCode)
                                        errorMessage = subjCode[2] +" in "+str( i.realsection)+ " Same Start Time"
                                        validRoom = False
                                        break
                                else:
                                    #room sched are not the same
                                    if inputStartTime >= roomEndTime:
                                        #Input Sched is After the sched in Database
                                        validRoom = True
                                    else:
                                        #Input Sched is not after the Sched in Database
                                        if inputEndTime <= roomStartTime:
                                            #Input Sched is earlier than Sched in Databse
                                            validRoom = True
                                        else:
                                            #Input Sched Conflict in DB Sched
                                            validRoom = False
                                            subjCode = str(i.subjectCode).split("|")
                                            print(subjCode)
                                            errorMessage = subjCode[2] + " in " + str(i.realsection) + " Time Overlap" 
                                            break 
                            else:
                                #No Day Exist in the room 
                                validRoom = True
                    else:
                        if studentScheduling.objects.filter(room = roomVacancy).count() == 0:
                            validRoom = True

                    limitless_rooms = ["NA", "N.A.", "N/A", "T.B.A.", "TBA", "MS TEAMS", "FIELD","Ms Teams","Field","GYM","Gym","MS Teams"]
                    print(limitless_rooms," in ", roomVacancy)
                    if roomVacancy.room in limitless_rooms:
                        validRoom = True

                    if validProf == True:
                        if validRoom == True:
                            formset.save()
                            validProf = False
                            validRoom = False
                            messages.success(request, 'Schedule successfully Added!')
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                        else:
                            messages.error(request, 'Room Time error: %s' % errorMessage)
                            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                    else:
                        messages.error(request, 'Faculty Time Error: %s' % errorMessage)
                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            else:
                formset.save()
                messages.success(request, 'Schedule successfully Added!')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'There is an error upon adding!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'chairperson/Stud_sched/cStudentSchedOnline2.html', {'formset': formset, 'schedule' :schedule})



def cStudentDeleteSched(request, block_id, sec_id):
    schedule = studentScheduling.objects.get(id = block_id)
    if request.method =='POST':
        schedule.delete()
        messages.success(request, 'Successfully removed!')
        return HttpResponseRedirect(reverse('cStudentSchedOnline2', args=(sec_id)))
    context = {'schedule': schedule}
    return render(request, 'chairperson/Stud_sched/cStudentDeleteSched.html', context)

#Study Plan Year of Admission
def studyplan1(request):
    id = request.user.id
    info = StudentInfo.objects.get(studentUser=id)
    instance = get_object_or_404(StudentInfo, studentUser=id)
    form = studyPlanForm(instance=instance)
    form.fields['curricula'].queryset = Curricula.objects.filter(departmentID=info.departmentID, schoolYr=info.studentCurriculum).order_by('id')

    '''if :
        magic = ""
    else:
        magic = "disabled"'''

    context = {
        'form': form,
        #'magic': magic,
    }

    if (request.method == 'POST'):
        if studyPlan.objects.filter(studentinfo=info).exists():
            studyPlan.objects.filter(studentinfo=info).update(admissionYr=info.studentCurriculum)
            instance = get_object_or_404(studyPlan, studentinfo=info)
            form = studyPlanForm(request.POST or None, instance=instance)
            if form.is_valid():
                form.save()
                return redirect('stdplnsub')
        else:
            stdpln = studyPlan(studentinfo=info, admissionYr=info.studentCurriculum)
            stdpln.save()
            instance = get_object_or_404(studyPlan, studentinfo=info)
            form = studyPlanForm(request.POST or None, instance=instance)
            if form.is_valid():
                form.save()
                return redirect('stdplnsub')
    
    return render(request, 'student/sOthers/sStudyplan1.html', context)

#Study Plan Subjects Taken
def studyplan2(request):
    id = request.user.id
    info = StudentInfo.objects.get(studentUser=id)
    semesters = Curricula.objects.all()
    subjects = courseList.objects.all()
    status = studyPlan.objects.get(studentinfo=info)
    context = {
        'info': info,
        'semesters': semesters,
        'subjects': subjects,
        'status': status,
    }

    if (request.method == 'POST'):
        if studyPlan.objects.filter(studentinfo=info).exists():
            failedsubs = request.POST.getlist('checkmark')
            studyPlan.objects.filter(studentinfo=info).update(failedsubs=failedsubs)
            return redirect('stdplnview')

    return render(request, 'student/sOthers/sStudyplan2.html', context)

def studyplan3(request):
    id = request.user.id
    info = StudentInfo.objects.get(studentUser=id)
    semesters = Curricula.objects.all()
    subjects = courseList.objects.all()
    status = studyPlan.objects.get(studentinfo=info)
    
    failedsubs = courseList.objects.filter(id__in=status.failedsubs)
    list = failedsubs.filter(curricula__cSem=status.curricula.cSem)
    fscourseCode = failedsubs.all().values_list('courseCode', flat=True)

    for semester in semesters:
        if semester == status.curricula:
            cCode = subjects.filter(curricula=semester, prerequisite__in=fscourseCode).values_list('courseCode', flat=True)
            cCode = [item.join("()") for item in cCode]
                #test = subjects.filter(curricula=semester).values_list('courseCode', 'id')

    context = {
        'info': info,
        'semesters': semesters,
        'subjects': subjects,
        'status': status,
        'list': list,
        'fscourseCode': fscourseCode,
        'cCode': cCode,
        #'test': test,
    }
    return render(request, 'student/sOthers/sStudyplan3.html', context)

def download_stdpln(request):
    id = request.user.id
    info = StudentInfo.objects.get(studentUser=id)
    status = studyPlan.objects.get(studentinfo=info)
    semesters = Curricula.objects.all()
    subjects = courseList.objects.all()

    failedsubs = courseList.objects.filter(id__in=status.failedsubs)
    list = failedsubs.filter(curricula__cSem=status.curricula.cSem)
    fscourseCode = failedsubs.all().values_list('courseCode', flat=True)

    for semester in semesters:
        if semester == status.curricula:
            cCode = subjects.filter(curricula=semester, prerequisite__in=fscourseCode).values_list('courseCode', flat=True)
            cCode = [item.join("()") for item in cCode]

    fsunits = list.filter().aggregate(total=Sum('courseUnit'))['total']
    ogunits = status.curricula.totalUnits
    #totalnum = fsunits + ogunits

    context = {
        'info': info,
        'status': status,
        'semesters': semesters,
        'subjects': subjects,
        'list': list,
        'fscourseCode': fscourseCode,
        'cCode': cCode,
        'ogunits': ogunits,
        #'totalnum': totalnum,
    }
    if status.studentinfo_id == info.studentUser_id:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] ='filename="StudyPlan_%s.pdf"' %(info.studentID)

        template = get_template('forms/download_stdpln.html')
        html = template.render(context)

        pisa_status = pisa.CreatePDF(
        html, dest=response)

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    else:
        messages.error(request,'No Copy Yet')
        return render(request,'student/sOthers/sStudyplan3.html')

def sptest(request):
    id = request.user.id
    info = StudentInfo.objects.get(studentUser=id)
    status = studyPlan.objects.get(studentinfo=info)
    semesters = Curricula.objects.all()
    subjects = courseList.objects.all()

    failedsubs = courseList.objects.filter(id__in=status.failedsubs)
    list = failedsubs.filter(curricula__cSem=status.curricula.cSem)
    fscourseCode = failedsubs.all().values_list('courseCode', flat=True)

    for semester in semesters:
        if semester == status.curricula:
            cCode = subjects.filter(curricula=semester, prerequisite__in=fscourseCode).values_list('courseCode', flat=True)
            cCode = [item.join("()") for item in cCode]

    fsunits = list.filter().aggregate(total=Sum('courseUnit'))['total']
    ogunits = status.curricula.totalUnits
    #totalnum = fsunits + ogunits

    context = {
        'info': info,
        'status': status,
        'semesters': semesters,
        'subjects': subjects,
        'list': list,
        'fscourseCode': fscourseCode,
        'cCode': cCode,
        'ogunits': ogunits,
        #'totalnum': totalnum,
    }

    return render(request, 'forms/download_stdpln.html', context)

def studyplan4(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        info = StudentInfo.objects.get(studentUser=id)
        if (request.method == 'POST'):
            spUpload = request.FILES.get('studyPlanUp')
            date = timezone.now() 
            try:
                applicant = spApplicant.objects.get(studentID_id=id)
                if applicant.remarks == "Returned":
                    if (request.method == 'POST'):
                        spUpload = request.FILES.get('studyPlanUp')
                        applicant.remarks = 'Submitted'
                        applicant.date = timezone.now() 
                        applicant.save()
                        return redirect('stdplncs') 
                else:
                    messages.error(request,'You have already submitted an application!')
                    return render(request,'student/sOthers/sStudyplan4.html')
            except ObjectDoesNotExist:
                sp_Applicant = spApplicant(studentID=info, sdplan=spUpload,date=date)
                sp_Applicant.save()
                return redirect('stdplncs')
        return render(request, 'student/sOthers/sStudyplan4.html')
    else:
            return redirect('index')

def studyplan5(request):
    return render(request, 'student/sOthers/sStudyplan5.html')


#manage faculty applicant
def cfaculty_applicant(request):
    if request.user.is_authenticated and request.user.is_chairperson:
        id= request.user.id
        info = FacultyInfo.objects.get(facultyUser=id)
        applicant = FacultyApplicant.objects.filter(department=info.departmentID.courseName)
        searchthis_query = request.GET.get('searchthis')
        if searchthis_query != " " and searchthis_query is not None:
            applicant  = applicant .filter(Q(firstName__icontains=searchthis_query) | Q(id__icontains=searchthis_query)| Q(lastName__icontains=searchthis_query)| Q(middleName__icontains=searchthis_query) | Q(remarks__icontains=searchthis_query)).distinct()
    return render(request, 'chairperson/cfaculty_applicant.html', {"applicant":applicant, "info": info})

def faculty_view(request, faculty_id):
    if request.method == 'GET':
        facultyapp = FacultyApplicant.objects.get(pk= faculty_id)
        return render(request, 'chairperson/faculty_view.html', {'facultyapp':facultyapp})
    elif request.method == 'POST':
        facultyapp = FacultyApplicant.objects.get(pk= faculty_id)
        statform = request.POST.get('slct')
        facultyapp.remarks = statform
        facultyapp.save()
        return redirect ('cfaculty_applicant')

def cfacultyapplicant_sortedlist(request):
    id = request.user.id
    info = FacultyInfo.objects.get(facultyUser=id)
    applicant = FacultyApplicant.objects.filter(department=info.departmentID.courseName)
    facultyapp_returned = FacultyApplicant.objects.filter(id__in=applicant).filter(remarks="Returned")
    facultyapp_submitted = FacultyApplicant.objects.filter(id__in=applicant).filter(remarks="Submitted")
    facultyapp_forwared = FacultyApplicant.objects.filter(id__in=applicant).filter(remarks="Forwarded")
    facultyapp_inprogress = FacultyApplicant.objects.filter(id__in=applicant).filter(remarks="In Progress")
    facultyapp_complete = FacultyApplicant.objects.filter(id__in=applicant).filter(remarks="Complete")

    context = {
        'info': info,
        'facultyapp_submitted': facultyapp_submitted,
        'facultyapp_returned': facultyapp_returned,
        'facultyapp_forwarded': facultyapp_forwared,
        'facultyapp_inprogress': facultyapp_inprogress,
        'facultyapp_complete': facultyapp_complete,
        'applicant' : applicant,

    }
    return render(request, 'chairperson/cfaculty_applicant-Master.html', context)

def emailApplicant(request,faculty_id):
    faculty = FacultyApplicant.objects.get(pk=faculty_id)
    email = faculty.email
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        html = request.POST.get('html')
        msg = EmailMultiAlternatives(f'{subject}',f'{content}', EMAIL_HOST_USER, ['cperson.dummy@gmail.com'], [f' {email}'])
        msg.attach_alternative(html, "text/html")
        msg.send()
        messages.success(request, "Message sent")
    return render(request, 'chairperson/emailApplicant.html', {'faculty':faculty})

def emailTrans(request,trans_id):
    trans = TransfereeApplicant.objects.get(pk=trans_id)
    email = trans.eadd
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        html = request.POST.get('html')
        msg = EmailMultiAlternatives(f'{subject}',f'{content}', EMAIL_HOST_USER, ['cperson.dummy@gmail.com'], [f' {email}'])
        msg.attach_alternative(html, "text/html")
        msg.send()
        messages.success(request, "Message sent")
    return render(request, 'chairperson/Others/emailApplicant-Transferee.html', {'trans':trans})

def emailShifter(request,shifter_id):
    shifter = ShifterApplicant.objects.get(pk=shifter_id)
    email = shifter.eadd
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        html = request.POST.get('html')
        msg = EmailMultiAlternatives(f'{subject}',f'{content}', EMAIL_HOST_USER, ['cperson.dummy@gmail.com'], [f' {email}'])
        msg.attach_alternative(html, "text/html")
        msg.send()
        messages.success(request, "Message sent")
    return render(request, 'chairperson/Others/emailApplicant-Shifter.html', {'shifter':shifter})


def sendmailfile(request, faculty_id):
    sends = FacultyApplicant.objects.get(pk=faculty_id)
    message = 'Message'
    subject = 'Subject'
    mail_id = sends.email
    mail_id1 = 'cperson.dummy@gmail.com'
    email = EmailMessage(subject, message, EMAIL_HOST_USER, [mail_id], [mail_id1])
    email.content_subtype = 'html'

    email.attach_file(os.path.join(settings.MEDIA_ROOT, sends.CV.name))
    email.attach_file(os.path.join(settings.MEDIA_ROOT, sends.certificates.name))
    email.attach_file(os.path.join(settings.MEDIA_ROOT, sends.credentials.name))
    email.attach_file(os.path.join(settings.MEDIA_ROOT, sends.TOR.name))

    email.send()
    messages.success(request,"Successfully sent!")
    return HttpResponseRedirect(reverse('faculty_view', args=(faculty_id)))

#TRANSFEREE APPLICANT
def transferee_1requirements(request):
    return render(request, './applicant/transferee_1requirements.html')

def transferee_2GWA(request):
    return render(request, './applicant/transferee_2GWA.html')

def transferee_2GWA(request):
    if (request.method == 'POST'):
        GWA = float(request.POST.get('GWA'))
        if (GWA <= 2.25 and GWA >= 1):
            return redirect('transferee_3GWAQual')
        else:
            return redirect('transferee_3.2GWANotQual')
    return render(request, './applicant/transferee_2GWA.html')

def transferee_3GWAQual(request):
    return render(request, './applicant/transferee_3GWAQual.html')

def transferee_3_2GWANotQual(request):
    return render(request, './applicant/transferee_3.2GWANotQual.html')

def transferee_9applicationform(request):
    if (request.method == 'POST'):
        try:
            studentID = request.POST.get("StudentNumber")
            department = request.POST.get("degree")
            lname = request.POST.get("LastName")
            fname = request.POST.get("FirstName")
            mname = request.POST.get("MiddleName")
            eadd = request.POST.get("EmailAddress")
            cnum = request.POST.get("Phone")
            studentStudyplan = request.FILES.get("studyPLan")
            studentNote = request.FILES.get("NoteofUndertaking")
            studentHD = request.FILES.get("HonorableDis")
            studentGoodmoral = request.FILES.get("GoodMoral")
            studentGrade = request.FILES.get("Grades")
            transfer_dateSubmitted = timezone.now()
            transferee = TransfereeApplicant(studentID=studentID, department=department, lname=lname, fname=fname, mname=mname, eadd=eadd, cnum=cnum, studentStudyplan=studentStudyplan, studentNote=studentNote, studentHD=studentHD, studentGoodmoral=studentGoodmoral, studentGrade=studentGrade,transfer_dateSubmitted=transfer_dateSubmitted)
            transferee.save()
            return redirect('transferee_10success')
        except:          
            messages.error(request,'You have already submitted an application!')
            return render(request,'./applicant/transferee_9applicationform.html')
    return render(request, './applicant/transferee_9applicationform.html')
    
def transferee_10success(request):
    return render(request, './applicant/transferee_10success.html')

#SHIFTER APPLICANT
def shifter1(request):
    return render(request, './applicant/shifter1.html')

def shifter2(request):
    return render(request, './applicant/shifter2.html')

def shifter2(request):
    if (request.method == 'POST'):
        GWA = float(request.POST.get('GWA'))
        if (GWA <= 2.25 and GWA >= 1):
            return redirect('shifter3')
        else:
            return redirect('shifter3.2')
    return render(request, './applicant/shifter2.html')

def shifter3(request):
    return render(request, './applicant/shifter3.html')

def shifter3_2(request):
    return render(request, './applicant/shifter3.2.html')

def shifter9(request):
    if (request.method == 'POST'):
        try:
            studentID = request.POST.get("StudID")
            department = request.POST.get("Deg")
            lname = request.POST.get("lname")
            fname = request.POST.get("fname")
            mname = request.POST.get("mname")
            eadd = request.POST.get("eadd")
            cnum = request.POST.get("cnum")
            studentshifterletter = request.FILES.get("LetterofIntentFile")
            studentGrade = request.FILES.get("GradeScreenshotFile")
            studentStudyplan = request.FILES.get("studyPlanFile")
            shifter_dateSubmitted = timezone.now()
            shiftee = ShifterApplicant(studentID=studentID, department=department, lname=lname, fname=fname, mname=mname, eadd=eadd, cnum=cnum, studentshifterletter=studentshifterletter, studentGrade=studentGrade, studentStudyplan=studentStudyplan,shifter_dateSubmitted=shifter_dateSubmitted)
            shiftee.save()
            return redirect('shifter10')
        except:          
            messages.error(request,'You have already submitted an application!')
            return render(request,'./applicant/shifter9.html')
    return render(request, './applicant/shifter9.html')
    
def shifter10(request):
    return render(request, './applicant/shifter10.html')

def GradesNotif(request):
    if request.user.is_authenticated and request.user.is_student:
        id= request.user.id
        acad = AcademicYearInfo.objects.all
        info = StudentInfo.objects.get(studentUser=id)
        try:
            notif_type = "GRADES SUBMISSION"
            feedback = crsGrade.objects.get(studentID=id)
            description = "Application Submission Feedback"
        except crsGrade.DoesNotExist:
            notif_type = "GRADES SUBMISSION"
            description = "No Submitted Application"
            feedback = None
        context = {'id': id,'acad':acad, 'info':info, 'feedback' : feedback, 'notif_type' : notif_type, 'description' : description }
        return render(request, 'student/sHome/sHomeNotifdetails.html', context) 
    else:
         return redirect('index')

def notifications(request, notification_id):
    fname = request.user.firstName
    mname = request.user.middleName
    lname = request.user.lastName
    notification = Notification.objects.get(pk=notification_id)
    notifications = get_notifications(request.user.id)
    print(notification.title)
    return render(request, 'chairperson/chairperson_notification.html', 
    {
        'fname' : fname,
        'mname' : mname,
        'lname' : lname,
        'notification' : notification,
        'notifications': notifications
    })

def pw_reset(request):
    if request.method == 'POST':
        password_form = PasswordResetForm(request.POST)
        if password_form.is_valid():
            data = password_form.cleaned_data['email']
            user_email = User.objects.filter(Q(email=data))
            if user_email.exists():
                for user in user_email:
                    subject = 'Password Reset Request'
                    email_template_name = 'pw_reset/password_message.txt'
                    parameters = {
                        'email': user.email,
                        'lastName': user.lastName,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'iPLM',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, parameters)
                    try:
                        send_mail(subject, email, '', [user.email], fail_silently=False)
                    except:
                        return HttpResponse('Invalid Header')
                    return redirect('password_reset_done')
    else:
        password_form = PasswordResetForm()
    context = {
        'password_form': password_form,
    }
    return render(request, 'pw_reset/password_reset.html', context)

def events(request, event_id=None):
    if not event_id == None:
        try:
            event = Event.objects.filter(pk=event_id).first()
        except Event.DoesNotExist:
            event = None
        return render(request, 'testfiles/event-view.html', {'event': event} )
    if not request.user.is_authenticated:
        return redirect('index')
    authorization = 'none'
    if request.user.is_chairperson: 
        authorization = 'chairperson'
    if request.user.is_student:
        authorization = 'student'
    events = Event.objects.all().order_by('eventStartDate')
    if request.GET.get('sortCategory'):
        events = Event.objects.filter(eventCategory=request.GET['sortCategory']).order_by('eventStartDate')
    return render(request, 'testfiles/event-test.html', {'authorization': authorization, 'events': events}) 

def eventsCreate(request):
    if request.user.is_authenticated and not request.user.is_chairperson:
        return redirect('events')
    if request.method == 'POST':
        try:
            event = Event(
                eventCategory=request.POST['eventCategory'],
                eventTitle=request.POST['eventTitle'],
                eventDescription=request.POST['eventDescription'],
                eventStartDate=request.POST['eventStartDate'],
                eventEndDate=request.POST['eventEndDate']
                )
            event.validate_frontend()
            event.save()
            messages.success(request, 'Event Created!')
            return redirect('events.create')
        except ValidationError as error:
            messages.error(request, error.message)
            return redirect('events.create')
    return render(request, 'testfiles/event-create.html')

# For rendering in homapages
def eventsComponent(request):
    if request.GET.get('sortCategory'):
        return Event.objects.filter(eventCategory=request.GET['sortCategory']).order_by('eventStartDate')
    return Event.objects.all().order_by('eventStartDate')