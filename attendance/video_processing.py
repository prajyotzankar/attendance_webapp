import os
from django.core.files.storage import default_storage
from .face_detection import face_detection_main
from .face_recognition import face_recognition_classsify
from .attendance_func import mark_attendance
model_dir = os.path.abspath("media/ml_models/20180402-114759/20180402-114759.pb")
classifier_filename_exp = os.path.abspath("media/ml_models/20180402-114759/my_classifier.pkl")

def handle_uploaded_file(f, time_slot_id):
    with open(default_storage.path(''+f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    images_array_out, images_names_out = face_detection_main(default_storage.path(''+f.name))
    present_students_PRN = face_recognition_classsify(images_array_out, images_names_out, model_dir, classifier_filename_exp)
    faculty_name, student_names, subject, time_slot, course_name = mark_attendance(present_students_PRN, time_slot_id)

    return faculty_name, student_names, subject, time_slot, course_name  
     
    