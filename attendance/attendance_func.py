import mysql.connector
from datetime import datetime
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from io import StringIO, BytesIO
from PIL import Image

conn_object = mysql.connector.connect(host='localhost', user='mit_wpu', database='mit_wpu_attendace', password='cbep.hYyvnDGR(gK')
cursor_object = conn_object.cursor()

#function to get attendance of a student by name
def get_attendance(student_name):
    """This function get the attendance of a student.
    Arguments:
    student_name : name of the student whose attendance to fetch.
    """
    
    """
    get the class id and subjects of all the class the student is enrolled in 
    using student name
    """
    query_class_id_subject = """select c.class_id, c.subject from class as c join student \
    as stu on c.course = stu.course and c.trimister = stu.trimister \
    and c.division = stu.division where stu.name = '%s'\
    """%(student_name)
    cursor_object.execute(query_class_id_subject)
    class_ids_subject = cursor_object.fetchall()

    #return false if the student name doesnt exist in database
    if class_ids_subject == []:
        return False
    """
    class_id_list = []
    for class_id, subject_name in class_ids_subject:
        for class_id in class_id:
            class_id = class_id
        class_id_list.append(class_id)
    print(class_id_list)
    """
    
    class_id_list = []
    for class_id, subject_name in class_ids_subject:
        class_id_list.append(class_id)
    
    
    
    get_roll_no_query = """select roll_no from student where name='%s'\
    """%(student_name)
    cursor_object.execute(get_roll_no_query)
    roll_no = cursor_object.fetchone()
    for roll_no in roll_no:
        roll_no = roll_no
    print(roll_no)
    column_name = "roll_no_" + str(roll_no)
    format_strings = ','.join(['%s'] * len(class_id_list))

    get_attendnace = "select class_id, date, %%s from attendance where class_id in (%s)"%(format_strings)
    params = (column_name,) + tuple(class_id_list)
    get_attendnace = get_attendnace%(params)
    cursor_object.execute(get_attendnace)
    attendance_ = cursor_object.fetchall()

    
    df_student_attend = pd.DataFrame(attendance_, columns=['class id', 'date', 'attendance'])
    df_student_attend['attendance'] = np.where(df_student_attend['attendance']==1, 'Present', 'Absent')
    
    
    subject = []
    for id in df_student_attend['class id']:
        subject += [item[1] for item in class_ids_subject if id in item]
    df_student_attend['subject'] = subject
    
    attendance = pd.DataFrame()

    attendance['subjects'] = df_student_attend['subject'].unique()

    total_lectures = []
    present_lectures = []
    for subject in attendance.subjects:
        total = len(df_student_attend[df_student_attend.subject == subject])
        present = len(df_student_attend[(df_student_attend.subject == subject) & (df_student_attend.attendance == 'Present')])
        total_lectures.append(total)
        present_lectures.append(present)

    attendance['total_lectures'] = total_lectures
    attendance['present'] = present_lectures
    attendance['percentage'] = (attendance['present']/attendance['total_lectures']*100).round(2)

    attendance.insert(0, 's_no', attendance.index+1)

    return attendance

def get_defaulter_list(course, trimister, division, subject, threshold):
    
    get_class_id_query = """select class_id from class where course='%s' and \
    trimister='%s' and division='%s' and subject='%s'"""
    params = (course, trimister, division, subject)
    get_class_id_query = get_class_id_query%(params)
    cursor_object.execute(get_class_id_query)
    class_id = cursor_object.fetchone()
    if class_id == None:
        return False
    
    for class_id in class_id:
        class_id = class_id
    
    get_names_and_roll_no_query = """select roll_no, name from student where course='%s' and trimister='%s' and division='%s'\
    """%(course, trimister, division,)
    cursor_object.execute(get_names_and_roll_no_query)
    names_and_roll_no = cursor_object.fetchall()
    
    params = []
    for i in range(1, len(names_and_roll_no)+1):
        column_name = 'roll_no_' + str(i)
        params.append(column_name)
    params.append(class_id)
    params = tuple(params)
    
    
    format_strings = ','.join(['%s'] * len(names_and_roll_no))
    get_full_attendance_query = """select %s from attendance where class_id='%%s'"""%(format_strings)
    get_full_attendance_query = get_full_attendance_query%(params)
    cursor_object.execute(get_full_attendance_query)
    full_attendance = cursor_object.fetchall()
    
    full_attendance_df = pd.DataFrame(full_attendance, columns=list(params)[:- 1])
    
    sums = []
    for sum in full_attendance_df.sum():
        sums.append(float(sum))
    
    
    attendance_df = pd.DataFrame(names_and_roll_no, columns=['roll_no', 'name']).sort_values(by=['roll_no'])
    attendance_df.reset_index(drop=True, inplace=True)                                                                                                                                                     
    attendance_df['attendance'] = [int(sum) for sum in sums]
    attendance_df['percent'] = (attendance_df['attendance']/len(full_attendance)*100).round(2)
    
    defaulter_attendance_df = attendance_df[attendance_df.percent <= threshold]
    if defaulter_attendance_df.empty:
        return False
    return defaulter_attendance_df




def get_defaulter_list_all_subjects(course, trimister, division, threshold):
    
    get_class_id_subject_query = """select class_id, subject from class where course='%s' and \
    trimister='%s' and division='%s' """
    params = (course, trimister, division,)
    get_class_id_subject_query = get_class_id_subject_query%(params)
    cursor_object.execute(get_class_id_subject_query)
    class_id_subject = cursor_object.fetchall()
    if class_id_subject == None:
        return False
    
    all_subject_defaulter_attendance_df = pd.DataFrame()
    
    get_names_and_roll_no_query = """select roll_no, name from student where course='%s' and trimister='%s' and division='%s'\
    """%(course, trimister, division,)
    cursor_object.execute(get_names_and_roll_no_query)
    names_and_roll_no = cursor_object.fetchall()
    
    for class_id, subject in class_id_subject:
        params = []
        for i in range(1, len(names_and_roll_no)+1):
            column_name = 'roll_no_' + str(i)
            params.append(column_name)
        params.append(class_id)
        params = tuple(params)


        format_strings = ','.join(['%s'] * len(names_and_roll_no))
        get_full_attendance_query = """select %s from attendance where class_id='%%s'"""%(format_strings)
        get_full_attendance_query = get_full_attendance_query%(params)
        cursor_object.execute(get_full_attendance_query)
        full_attendance = cursor_object.fetchall()

        full_attendance_df = pd.DataFrame(full_attendance, columns=list(params)[:- 1])

        sums = []
        for sum in full_attendance_df.sum():
            sums.append(float(sum))


        attendance_df = pd.DataFrame(names_and_roll_no, columns=['roll_no', 'name']).sort_values(by=['roll_no'])
        attendance_df.reset_index(drop=True, inplace=True)                                                                                                                                                     
        attendance_df['attendance'] = [int(sum) for sum in sums]
        attendance_df['percent'] = (attendance_df['attendance']/len(full_attendance)*100).round(2)
        attendance_df.drop('attendance', axis=1, inplace=True)
        attendance_df['subject'] = [subject]*(attendance_df.shape[0])
        defaulter_attendance_df = attendance_df[attendance_df.percent <= threshold]
        
        if defaulter_attendance_df.empty:
            pass
        else:
            all_subject_defaulter_attendance_df = all_subject_defaulter_attendance_df.append(defaulter_attendance_df)
        
        
    if all_subject_defaulter_attendance_df.empty:
        return False
    
    all_subject_defaulter_attendance_df.reset_index(drop=True, inplace=True)
    all_subject_defaulter_attendance_df = all_subject_defaulter_attendance_df.groupby(['subject', 'name']).percent.max()
    all_subject_defaulter_attendance_df = pd.DataFrame(all_subject_defaulter_attendance_df)
    
    return all_subject_defaulter_attendance_df



def plot_graph(df):

    fig = plt.figure(facecolor='#131111')
    x = df['subjects']
    y = df['percentage']

    mask_1 = y <= 75
    mask_2 = y > 75

    plt.title("Attendance bar plot", color='white')
    plt.ylabel('Subjects', color='white')
    plt.xlabel('Percentage', color='white')
    
    """plt.rcParams.update({'text.color' : "white",
                     'axes.labelcolor' : "white",
                     'xtick.color' : "white",
                     'ytick.color' : "white"})"""

    
    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
                     
    height = len(df)
    plt.axvline(75, linewidth=2, color='white',label='75%')
    colors = {'Low Attendance':'#890909', 'Normal':'#808080', '75% Line':'white' }         
    labels = list(colors.keys())
    handles = [plt.Rectangle((0,0),1,1, color=colors[label]) for label in labels]
    plt.legend(handles, labels, facecolor='black', loc='lower right', 
            fancybox=True, shadow=True, labelcolor='white')

    plt.barh(x[mask_1], y[mask_1], height=0.4, align='center', color='#890909')
    plt.barh(x[mask_2], y[mask_2], height=0.4, align='center', color='#808080')
    ax = plt.gca()
    ax.set_facecolor(('#131111'))

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data


def mark_attendance(list_prn_of_people_present, time_slot_id):
    
    """this is a function to mark attendance of 
        students present in the class"""
    """Arguments:
        list_prn_of_people_present : list of prn of students and faculty present in the class.
        time_slot_id : time_slot id based on the time the class was conducted.
    """

    """get the faculty PRN from list of PRN"""
    faculty_PRN = [PRN for PRN in list_prn_of_people_present if list(PRN)[0] == 'E']
    print(list_prn_of_people_present)
    for PRN in faculty_PRN:
        list_prn_of_people_present.remove(PRN)
    faculty_PRN = faculty_PRN[0]

    faculty_PRN = ''.join(filter(str.isdigit, faculty_PRN))
    students_PRN = [''.join(filter(str.isdigit, PRN)) for PRN in list_prn_of_people_present]

    """get the faculty name PRN number using PRN number"""
    get_faculty_name= """select name from faculty where \
    PRN = '%s'"""%(faculty_PRN)
    
    cursor_object.execute(get_faculty_name)
    faculty_name = cursor_object.fetchone()
    for faculty_name in faculty_name:
        faculty_name = faculty_name
    print(faculty_name)
    
    
    """get the class id using faculty PRN and student present PRN"""
    query_class_id_subject = """select c.class_id, c.subject from class as c join student \
    as stu on c.course = stu.course and c.trimister = stu.trimister \
    and c.division = stu.division where stu.PRN = '%s' and \
    c.PRN = '%s'"""%(students_PRN[0], faculty_PRN)
    
    cursor_object.execute(query_class_id_subject)
    class_id_subject = cursor_object.fetchone()
    (class_id, subject) = class_id_subject
    print(class_id, subject)
    

    """Get Course"""
    query_course = """select course from class where class_id = '%s'"""%(class_id)
    cursor_object.execute(query_course)
    course_name = cursor_object.fetchone()
    for course_name in course_name:
        course_name = course_name

    """get the roll numbers of the students present in the class"""
    roll_no_list = []
    student_names = []
    for student_PRN in students_PRN:
        get_roll_no_name_query = """select roll_no, name from student where PRN='%s'\
        """%(student_PRN)
        cursor_object.execute(get_roll_no_name_query)
        roll_no_name = cursor_object.fetchone()
        roll_no, student_name = roll_no_name
        roll_no_list.append(roll_no)
        student_names.append(student_name)
    print(roll_no_list, student_names)
    

    """get time slot from time_slot _id"""
    query_time_begin_duration = """select * from time_table where time_slot_uid = '%s'"""%(time_slot_id)
    cursor_object.execute(query_time_begin_duration)
    time_begin_duration = cursor_object.fetchone()
    _, time_begin, duration = time_begin_duration
    print(time_begin, duration)
    
    time_end = time_begin + 100*(duration//60)
    time_begin_end = [time_begin, time_end]
    for i in range(2):
        time_begin_end[i] =  list(str(time_begin_end[i]))
        time_begin_end[i].insert(-2, ":")
        time_begin_end[i] = "".join(time_begin_end[i])
        time_begin_end[i] = time.strptime(time_begin_end[i], "%H:%M")
        time_begin_end[i]= time.strftime("%I:%M %p", time_begin_end[i])
        
    time_slot = time_begin_end[0] + " - " + time_begin_end[1]
    print(time_slot)

    
    attendance_list = [0] * 20
    for i in range(len(roll_no_list)):
        attendance_list[roll_no_list[i] - 1] = 1
    print(attendance_list)
    
    #get the durrent date YYYYMMDD
    date = datetime.now().date()
    
    """insert the attendace of students in the attendance table"""
    query_insert_attendance = """insert into attendance \
    (class_id, time_slot_uid, date, roll_no_1, roll_no_2, roll_no_3, roll_no_4, roll_no_5, roll_no_6, \
    roll_no_7, roll_no_8, roll_no_9, roll_no_10, roll_no_11, roll_no_12, roll_no_13, roll_no_14, \
    roll_no_15, roll_no_16, roll_no_17, roll_no_18, roll_no_19, roll_no_20) \
    values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', \
    '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s') \
    """%(class_id, time_slot_id, date, attendance_list[0], attendance_list[1], \
         attendance_list[2], attendance_list[3], attendance_list[4], attendance_list[5], \
         attendance_list[6], attendance_list[7], attendance_list[8], attendance_list[9], \
         attendance_list[10], attendance_list[11], attendance_list[12], attendance_list[13], \
         attendance_list[14], attendance_list[15], attendance_list[16], attendance_list[17], \
         attendance_list[18], attendance_list[19])
    cursor_object.execute(query_insert_attendance)
    conn_object.commit()

    return faculty_name, student_names, subject, time_slot, course_name