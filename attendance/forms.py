from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

TIME_SLOT_CHOICE= [
    ('10007', '9:00 AM - 10:00 AM'),
    ('10006', '9:30 AM - 10:30 AM'),
    ('10000', '10:00 AM - 11:00 AM'),
    ('10001', '11:15 AM - 12:15 PM'),
    ('10002', '12:45 PM - 3:45 PM'),
    ('10003', '12:45 PM - 1:45 PM'),
    ('10004', '1:00 PM - 2:00 PM'),
    ('10005', '3:15 PM - 4:15 PM'),
    
    ]
class UploadFileForm(forms.Form):
    #title = forms.CharField(max_length=50)
    #time_slot_id = forms.CharField(max_length=6)
    time_slot_id= forms.CharField(label='Time Slot', widget=forms.Select(choices=TIME_SLOT_CHOICE))
    file = forms.FileField()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



