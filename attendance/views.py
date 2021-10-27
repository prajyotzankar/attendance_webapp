import csv
import json
import pandas as pd
from math import ceil, sqrt, floor
import numpy as np

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse


from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

#user def functions
from .video_processing import handle_uploaded_file
from .attendance_func import get_attendance, get_defaulter_list, plot_graph
from .attendance_func import get_defaulter_list_all_subjects
from .forms import UploadFileForm, UserRegisterForm
 




def logout_view(request):
    logout(request)
    return redirect('login')

# our home page view
@login_required(login_url='/')
def home(request):
    return render(request, 'home.html')

#error messages customization
def error_500(request):
        context = {'error_number' : '500', 'error_name' : 'Server Error'}
        return render(request,'show_error.html', context)

def error_404(request, exception):
        context = {'error_number' : '404', 'error_name' : 'Page Not Found'}
        return render(request,'show_error.html', context)

def error_403(request, exception):
        context = {'error_number' : '403', 'error_name' : 'Forbidden'}
        return render(request,'show_error.html', context)

def error_400(request, exception):
        context = {'error_number' : '400', 'error_name' : 'Bad Request'}
        return render(request,'show_error.html', context)

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student Registered")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form" : form})


@login_required(login_url='/')
def profile(request):    
    return render(request, 'profile.html')
    

@login_required(login_url='/')
def attendance(request):
    
    if request.method=='POST':
        student_name = request.POST['Name']
        df_att = get_attendance(student_name)
        """isinstance(df_att, pd.DataFrame)"""
        if isinstance(df_att, pd.DataFrame):
            # parsing the DataFrame in json format.
            json_records = df_att.reset_index().to_json(orient ='records')
            data = []
            data = json.loads(json_records)
            #get the graph of dataframe in base64
            graph = plot_graph(df_att)

            context = {'student_name': student_name, 'd': data, 'plot': graph}

            return render(request, 'attendance.html', context)
        else:
            error = {'error' : "Name not found in Database."}
            return render(request, 'attendance.html', error)
    return render(request, 'attendance.html')

def get_course_label(course):
    if course == 99:
        return "Course"
    elif course == 100:
        return "BSc. CS"
    elif course == 101:
        return "BSc. Statistics"
    elif course == 102:
        return "MSc. Statistics"
    elif course == 103:
        return "MSc. CS"
    elif course == 300:
        return "MBA"

@login_required(login_url='/')
def defaulter(request):
    if request.method=='POST':
        course = int(request.POST['course'])
        trimister = int(request.POST['trimister'])
        division = int(request.POST['division'])
        subject = request.POST['subject']
        threshold = int(request.POST['threshold'])
        course_label = get_course_label(course)

        if subject == "ALL":
            defaulter_list_df = get_defaulter_list_all_subjects(course, trimister, division, threshold)
        else:
            defaulter_list_df = get_defaulter_list(course, trimister, division, subject, threshold)


        form_inputs = {'course':course, 'trimister':trimister, 'division':division, \
            'subject':subject, 'threshold':threshold, 'course_label':course_label}
        if isinstance(defaulter_list_df, pd.DataFrame):
            # parsing the DataFrame in json format.
            json_records = defaulter_list_df.reset_index().to_json(orient ='records')
            data = []
            data = json.loads(json_records)
            context = {'d': data, 'form_inputs':form_inputs}
            
            return render(request, 'defaulter.html', context)
        else:
            error = {'error' : "No Defaulter", 'form_inputs':form_inputs}
            return render(request, 'defaulter.html', error)

    return render(request, 'defaulter.html')

@login_required(login_url='/')
def defaulter_list(request):

    if request.method=='POST':
        course = int(request.POST['course'])
        trimister = int(request.POST['trimister'])
        division = int(request.POST['division'])
        subject = request.POST['subject']
        threshold = int(request.POST['threshold'])
        course_label = get_course_label(course)

        form_inputs = {'course':course, 'trimister':trimister, 'division':division, \
            'subject':subject, 'threshold':threshold, 'course_label':course_label}
    
        file_name = str(course_label) + "_" + str(trimister) + "_" + str(division) \
            + "_" + str(subject) + ".csv"
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(file_name)},
        )


        if subject == "ALL":
            defaulter_list_df = get_defaulter_list_all_subjects(course, trimister, division, threshold)
        else:
            defaulter_list_df = get_defaulter_list(course, trimister, division, subject, threshold)


        if isinstance(defaulter_list_df, pd.DataFrame):
            defaulter_list_df.to_csv(path_or_buf=response,sep=',',float_format='%.2f',decimal=".")
            return response
        else:
            error = {'error' : "No Defaulter", 'form_inputs':form_inputs}
            return render(request, 'defaulter.html', error)

    return render(request, 'defaulter.html')
    


@login_required(login_url='/')       
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        file_size = request.FILES['file'].size
        file_type = request.FILES['file'].content_type
        allowed_file_type = ['video/mp4', 'video/mkv']

        if file_size not in range(1000000, 100000000) or file_type not in allowed_file_type:
            form = UploadFileForm()
            error = {'error' : "Upload only MP4/MKV file under 100MB", 'form':form}
            return render(request, 'upload.html', error)
        elif form.is_valid(): 
            
            time_slot_id = int(request.POST['time_slot_id'])
            faculty_name, student_names, subject, time_slot, course_name = handle_uploaded_file(request.FILES['file'], time_slot_id)
            #faculty_name, student_names, subject, time_slot = handle_uploaded_file(request.FILES['file'], 10002)

            """student_names = ['Lyle', 'Alejandra', 'Jake', 'Kimberly', 'James', 'Lauren', 'David', \
                'Sayed', 'Tuka', 'Claire', 'Lauren', 'Will', 'Lailah', 'Joao', 'Ronnie', 'Nick',
                'Prajyot', 'Kumar']
            faculty_name = "Tsedal Neeley"
            subject = "MBA"
            time_slot = "12:45 PM - 03:45 PM"
            """
            
            
            no_of_rows = ceil(len(student_names)/4)
            for i in range(no_of_rows*4 - len(student_names)):
                student_names.append("")
            arr_of_stu_names = np.reshape(student_names, (-1, 4))
            df_of_stu_names = pd.DataFrame(arr_of_stu_names)
            df_of_stu_names = df_of_stu_names.reset_index()
            json_records = df_of_stu_names.reset_index().to_json(orient ='records')
            table_of_stu_names = []
            table_of_stu_names = json.loads(json_records)
            
            course_label = get_course_label(course_name)
            form = UploadFileForm()
            context = {'faculty_name': faculty_name, 'student_names': table_of_stu_names,\
                'subject':subject, 'time_slot':time_slot, 'form':form, 'course_name':course_label}
    
            return render(request, 'upload.html', context)

        else:
            form = UploadFileForm()
            error = {'error' : "ERROR", 'form':form}
            return render(request, 'upload.html', error)
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})





"""def demo_view(request):
	# If method is POST, process form data and start task
	if request.method == 'POST':
		# Create Task
		download_task = ProcessDownload.delay()
		# Get ID
		task_id = download_task.task_id
		# Print Task ID
		print(f'Celery Task ID: {task_id}')
		# Return demo view with Task ID
		return render(request, 'progress.html', {'task_id': task_id})
	else:
		# Return demo view
		return render(request, 'progress.html', {})"""



