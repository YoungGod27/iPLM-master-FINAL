from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django_admin_listfilter_dropdown.filters import ( DropdownFilter, ChoiceDropdownFilter, RelatedDropdownFilter )

from .models import *

#DON'T TOUCH ^^
admin.site.site_header = 'iPLM Admin Site'
admin.site.index_title = 'Database Tables'
admin.site.site_title = 'iPLM Administration'

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'firstName', 'middleName', 'lastName')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """
    #password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'firstName', 'middleName',
                  'lastName', 'is_active', 'is_admin', 'is_chairperson', 'is_faculty', 'is_student')


class FacultyInfoInline(admin.StackedInline):
    # To add fields from Faculty database to User creation in Admin Site
    model = FacultyInfo
    can_delete = False
    verbose_name_plural = 'Faculty Profile'
    fk_name = 'facultyUser'

class StudentInfoInline(admin.StackedInline):
    # To add fields from Faculty database to User creation in Admin Site
    model = StudentInfo
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'studentUser'

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    inlines = [FacultyInfoInline, StudentInfoInline]  # Add other InLine for cperson, student, etc...

    ''' The fields to be used in displaying the User model.
     These override the definitions on the base UserAdmin
     that reference specific fields on auth.User.
     '''
    list_display = ('email', 'firstName', 'middleName', 'lastName',
                    'is_active', 'is_admin', 'is_chairperson', 'is_faculty', 'is_student')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('firstName', 'middleName', 'lastName')}),
        ('Permissions', {'fields': ('is_active', 'is_admin', 'is_chairperson', 'is_faculty', 'is_student')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',
                       'firstName', 'middleName', 'lastName', 'is_admin', 'is_chairperson', 'is_faculty', 'is_student'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()



# CHAIRPERSON ADMIN
class ChairpersonInfoAdmin(admin.ModelAdmin):
    model = ChairpersonInfo
    list_display = ('get_id', 'get_email', 'get_lname', 'get_fname', 'get_mname')

    def get_email(self, obj):
        return obj.cpersonUser.email

    get_email.short_description = 'Email'

    def get_id(self, obj):
        return obj.cpersonUser.id

    get_id.short_description = 'ID'

    def get_fname(self, obj):
        return obj.cpersonUser.firstName

    get_fname.short_description = 'First Name'

    def get_lname(self, obj):
        return obj.cpersonUser.lastName

    get_lname.short_description = 'Last Name'

    def get_mname(self, obj):
        return obj.cpersonUser.middleName

    get_mname.short_description = 'Middle Name'



# FACULTY ADMIN
class FacultyInfoAdmin(admin.ModelAdmin):
    search_fields = ['facultyID', 'facultyUser__email', 'facultyUser__firstName', 'facultyUser__lastName','facultyUser__middleName']
    model = FacultyInfo
    list_display = ('get_id', 'get_email', 'get_lname', 'get_fname', 'get_mname')

    def get_email(self, obj):
        return obj.facultyUser.email

    get_email.short_description = 'Email'

    def get_id(self, obj):
        return obj.facultyUser.id

    get_id.short_description = 'ID'

    def get_fname(self, obj):
        return obj.facultyUser.firstName

    get_fname.short_description = 'First Name'

    def get_lname(self, obj):
        return obj.facultyUser.lastName

    get_lname.short_description = 'Last Name'

    def get_mname(self, obj):
        return obj.facultyUser.middleName

    get_mname.short_description = 'Middle Name'



# STUDENT ADMIN
class StudentInfoAdmin(admin.ModelAdmin):
    search_fields = ['studentID', 'studentUser__email', 'studentUser__firstName', 'studentUser__lastName','studentUser__middleName']
    model = StudentInfo
    list_display = ('get_id', 'get_email', 'get_lname', 'get_fname', 'get_mname',)

    def get_email(self, obj):
        return obj.studentUser.email

    get_email.short_description = 'Email'

    def get_id(self, obj):
        return obj.studentUser.id

    get_id.short_description = 'ID'

    def get_fname(self, obj):
        return obj.studentUser.firstName

    get_fname.short_description = 'First Name'

    def get_lname(self, obj):
        return obj.studentUser.lastName

    get_lname.short_description = 'Last Name'

    def get_mname(self, obj):
        return obj.studentUser.middleName

    get_mname.short_description = 'Middle Name'

# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# Register ProfileInfo and ProfileInfoAdmin
admin.site.register(ChairpersonInfo, ChairpersonInfoAdmin)
admin.site.register(FacultyInfo, FacultyInfoAdmin)
admin.site.register(StudentInfo, StudentInfoAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)



#AcademicInfo
class AcademicYearInfoAdmin(admin.ModelAdmin):
    model = AcademicYearInfo
    list_display = ('get_id', 'yearstarted','yearended','semester')

    def get_id(self, obj):
        return obj.id

    def yearstarted(self, obj):
        return obj.yearstarted

    def yearended(self, obj):
        return obj.yearended

    def semester(self, obj):
        return obj.semester

    def has_delete_permission(self, request, obj=None):
        # Disable delete
        return True

    def has_add_permission(self, request, obj=None):
        return True

admin.site.register(AcademicYearInfo, AcademicYearInfoAdmin)



#COLLEGE INFO
class CollegeAdmin(admin.ModelAdmin):
    model = College
    list_display = ('get_id', 'collegeName','collegeDesc')

    def get_id(self, obj):
        return obj.id

    def collegeName(self, obj):
        return obj.collegeName

    def collegeDesc(self, obj):
        return obj.collegeDesc

    list_filter = [('collegeName',DropdownFilter)]

admin.site.register(College, CollegeAdmin)


#DEPARTMENT
class DepartmentAdmin(admin.ModelAdmin):
    model =Department
    list_display = ('get_id', 'collegeId','courseName','courseDesc','chairperson')

    def get_id(self, obj):
        return obj.id

    def collegeId(self, obj):
        return obj.collegeId.collegeName

    def courseName(self, obj):
        return obj.courseName

    def chairperson(self, obj):
        return obj.chairperson

    list_filter = [('collegeId',RelatedDropdownFilter)]

admin.site.register(Department, DepartmentAdmin)



#BLOCK SECTION
class BlockSectionAdmin(admin.ModelAdmin):
    model = BlockSection
    list_display = ('get_id', 'blockCourse','blockYear','blockSection','adviser')

    def get_id(self, obj):
        return obj.id

    def blockCourse(self, obj):
        return obj.blockCourse

    def blockYear(self, obj):
        return obj.blockYear

    def blockSection(self, obj):
        return obj.blockSection

    def adviser(self, obj):
        return obj.adviser
    
    #list_filter = ('blockCourse','blockYear','adviser')
    list_filter = [('blockCourse',DropdownFilter),('blockYear',ChoiceDropdownFilter),('adviser',RelatedDropdownFilter)]

admin.site.register(BlockSection, BlockSectionAdmin)



#SUBJECT INFO
class subjectInfoAdmin(admin.ModelAdmin):
    model = subjectInfo
    list_display = ('get_id', 'subjectCode','subjectName','subjectPrerequisite','yearstanding','college')

    def get_id(self, obj):
        return obj.id

    def subjectCode(self, obj):
        return obj.subjectCode

    def subjectName(self, obj):
        return obj.subjectName

    def subjectPrerequisite(self, obj):
        return obj.subjectPrerequisite

    def yearstanding(self, obj):
        return obj.yearstanding 

    def college(self, obj):
        return obj.college.collegeName

    #list_filter = ('subjectCode','subjectName','yearstanding','college')

    list_filter = [('subjectCode',DropdownFilter),('subjectName',DropdownFilter),('yearstanding',DropdownFilter),('college',RelatedDropdownFilter )]


admin.site.register(subjectInfo, subjectInfoAdmin)



#CURRICULUM INFORMATION
class curriculumInfoAdmin(admin.ModelAdmin):
    model = curriculumInfo
    list_display = ('get_id','schoolYear','schoolSem','subject','subjectUnits','subjectPrequisite','yearstanding')

    def get_id(self, obj):
        return obj.id

    def schoolYear(self, obj):
        return obj.schoolYear

    def schoolSem(self, obj):
        return obj.schoolSem

    def subject(self, obj):
        return obj.subjectCode

    def subjectUnits(self, obj):
        return obj.subjectUnits

    def subjectPrequisite(self, obj):
        return obj.subjectCode.subjectPrerequisite

    def yearstanding(self, obj):
        return obj.subjectCode.yearstanding

    #list_filter = ('subjectCode','subjectName','yearstanding','college')

    list_filter = [('curriculumyear',DropdownFilter),('departmentID',RelatedDropdownFilter),('subjectCode',RelatedDropdownFilter),('schoolYear',ChoiceDropdownFilter), ('schoolSem',ChoiceDropdownFilter)]

admin.site.register(curriculumInfo, curriculumInfoAdmin)



#STUDENT CHECKLIST AND GRADE
class currchecklistAdmin(admin.ModelAdmin):
    search_fields = ['owner__studentID']
    model = currchecklist
    list_display = ('get_id','owner','curriculum','yearTaken','semTaken')

    def get_id(self, obj):
        return obj.id

    def owner(self, obj):
        return obj.owner

    def curriculum(self, obj):
        return obj.curriculumCode.subjectCode.subjectName

    def subjectGrades(self, obj):
        return obj.subjectGrades

    def yearTaken(self, obj):
        return obj.yearTaken

    def semTaken(self, obj):
        return obj.semTaken

    #list_filter = ('subjectCode','subjectName','yearstanding','college')

    list_filter = [('owner',RelatedDropdownFilter)]

admin.site.register(currchecklist, currchecklistAdmin)



#CRS GRADE FILE
class crsGradeAdmin(admin.ModelAdmin):
    search_fields = ['studentID__studentID']
    model = crsGrade
    list_display = ('get_id','studentID','firstname','MiddleName','LastName','ApplicationStatus')

    def get_id(self, obj):
        return obj.id

    def studentID(self, obj):
        return obj.studentID

    def firstname(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.middleName

    def ApplicationStatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',RelatedDropdownFilter),('studentID__studentCourse',DropdownFilter),('remarks',DropdownFilter)]


admin.site.register(crsGrade, crsGradeAdmin)



#BLOCK SCHEDULING
class studentSchedulingAdmin(admin.ModelAdmin):
    model = studentScheduling
    list_display = ('get_id', 'subjectCode','section','instructor','day','timeStart','timeEnd','room','type','realsection')

    def get_id(self, obj):
        return obj.id

    def subjectCode(self, obj):
        return obj.subjectCode

    def section(self, obj):
        return obj.section

    def instructor(self, obj):
        return obj.instructor

    def day(self, obj):
        return obj.day

    def timeStart(self, obj):
        return obj.timeStart

    def timeEnd(self, obj):
        return obj.timeEnd

    def room(self, obj):
        return obj.room

    def type(self, obj):
        return obj.type

    def realsection(self, obj):
        return obj.realsection

    list_filter = [('subjectCode',RelatedDropdownFilter),('subjectCode__blockCourse',DropdownFilter),('section',DropdownFilter),('instructor',RelatedDropdownFilter),('day',ChoiceDropdownFilter),('timeStart',DropdownFilter),('timeEnd',DropdownFilter),('room',DropdownFilter),('type',ChoiceDropdownFilter),('realsection',RelatedDropdownFilter)]

    #list_filter = ('subjectCode','section','instructor','day','timeStart','timeEnd','room','type','realsection')

admin.site.register(studentScheduling, studentSchedulingAdmin)
admin.site.register(RoomInfo)


# HD STUDENT APPLICANT
class hdApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID__studentID']
    model = hdApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','status','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.studentID.studentCourse

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.lastName

    def status(self, obj):
        return obj.studentID.studentRegStatus

    def Applicationstatus(self, obj):
        return obj.remarks


    list_filter = [('studentID',RelatedDropdownFilter),('studentID__departmentID__courseName',DropdownFilter),('remarks',DropdownFilter)]

admin.site.register(hdApplicant, hdApplicantAdmin)


# OJT STUDENT APPLICANT
class OjtApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID__studentID']
    model = OjtApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','status','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.studentID.studentCourse

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.lastName

    def status(self, obj):
        return obj.studentID.studentRegStatus

    def Applicationstatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',RelatedDropdownFilter),('remarks',DropdownFilter),('studentID__departmentID__courseName',DropdownFilter)]

admin.site.register(OjtApplicant, OjtApplicantAdmin)



# SP STUDENT APPLICANT
class spApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID__studentID']
    model = spApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','status','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.studentID.studentCourse

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.lastName

    def status(self, obj):
        return obj.studentID.studentRegStatus

    def Applicationstatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',RelatedDropdownFilter),('studentID__departmentID__courseName',DropdownFilter),('remarks',DropdownFilter)]

admin.site.register(spApplicant, spApplicantAdmin)


# LOA STUDENT APPLICANT
class LOAApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID__studentID']
    model = LOAApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','status','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.studentID.studentCourse

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.lastName

    def status(self, obj):
        return obj.studentID.studentRegStatus

    def Applicationstatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',RelatedDropdownFilter),('studentID__studentCourse',DropdownFilter),('remarks',DropdownFilter)]

admin.site.register(LOAApplicant, LOAApplicantAdmin)



# SHIFTER STUDENT APPLICANT
class ShifterApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID', 'lname', 'fname', 'mname','eadd']
    model = ShifterApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.department

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.fname

    def MiddleName(self, obj):
        return obj.mname

    def LastName(self, obj):
        return obj.lname

    def Applicationstatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',DropdownFilter),('remarks',DropdownFilter)]

admin.site.register(ShifterApplicant, ShifterApplicantAdmin)



# TRANSFEREE STUDENT APPLICANT
class TransfereeApplicantAdmin(admin.ModelAdmin):
    search_fields = ['studentID', 'lname', 'fname', 'mname','eadd']
    model = TransfereeApplicant
    list_display = ('get_id','course','studentID','FirstName','MiddleName','LastName','Applicationstatus')

    def get_id(self, obj):
        return obj.id

    def course(self, obj):
        return obj.department

    def studentID(self, obj):
        return obj.studentID

    def FirstName(self, obj):
        return obj.fname

    def MiddleName(self, obj):
        return obj.mname

    def LastName(self, obj):
        return obj.lname

    def Applicationstatus(self, obj):
        return obj.remarks

    list_filter = [('studentID',DropdownFilter),('remarks',DropdownFilter)]

admin.site.register(TransfereeApplicant, TransfereeApplicantAdmin)


# FACULTY APPLICANT
admin.site.register(FacultyApplicant),



#STUDENT APPLICATION FORM FILL-UP
class hdClearanceFormAdmin(admin.ModelAdmin):
    model = hdClearanceForm
    list_display = ('get_id','studentID','firstname','MiddleName','LastName')

    def get_id(self, obj):
        return obj.id

    def studentID(self, obj):
        return obj.studentID

    def firstname(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.middleName

    list_filter = [('studentID',DropdownFilter)]

admin.site.register(hdClearanceForm, hdClearanceFormAdmin)


class hdTransferCertAdmin(admin.ModelAdmin):
    model = hdTransferCert
    list_display = ('get_id','studentID','firstname','MiddleName','LastName')

    def get_id(self, obj):
        return obj.id

    def studentID(self, obj):
        return obj.studentID

    def firstname(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.middleName

    list_filter = [('studentID',DropdownFilter)]

admin.site.register(hdTransferCert, hdTransferCertAdmin)



class loaClearanceFormAdmin(admin.ModelAdmin):
    model = loaClearanceForm
    list_display = ('get_id','studentID','firstname','MiddleName','LastName')

    def get_id(self, obj):
        return obj.id

    def studentID(self, obj):
        return obj.studentID

    def firstname(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.middleName

    list_filter = [('studentID',DropdownFilter)]

admin.site.register(loaClearanceForm, loaClearanceFormAdmin)



class loaFormAdmin(admin.ModelAdmin):
    model = loaForm
    list_display = ('get_id','studentID','firstname','MiddleName','LastName')

    def get_id(self, obj):
        return obj.id

    def studentID(self, obj):
        return obj.studentID

    def firstname(self, obj):
        return obj.studentID.studentUser.firstName

    def MiddleName(self, obj):
        return obj.studentID.studentUser.middleName

    def LastName(self, obj):
        return obj.studentID.studentUser.middleName

    list_filter = [('studentID',DropdownFilter)]

admin.site.register(loaForm, loaFormAdmin)

admin.site.register(HD_DroppingForm)

#Study Plan
class CurriculaAdmin(admin.ModelAdmin):
    search_fields = ['departmentID__courseName', 'cYear']

class courseListAdmin(admin.ModelAdmin):
    list_display = ['get_departmentID', 'courseCode', 'courseName', 'courseUnit', 'prerequisite', 'counted_in_GWA']

    def get_departmentID(self, obj):
        return obj.curricula.departmentID
    get_departmentID.admin_order_field = 'curricula__departmentID'
    get_departmentID.short_description = 'Department'

    search_fields = ['curricula__departmentID__courseName', 'courseCode', 'courseName']

admin.site.register(Curricula, CurriculaAdmin),
admin.site.register(courseList, courseListAdmin),
admin.site.register(studyPlan),

class NotificationAdmin(admin.ModelAdmin): 
    list_display = ['user_id', 'title', 'description', 'status', 'created_at']

admin.site.register(Notification, NotificationAdmin) 