# Facial Recognition Attendance System 

**Problem Statement**

Attendance marking in a classroom during a lecture is not only burdensome but also a time-consuming task. Old-school attendance systems are no longer efficient enough for keeping track of student attendance. Sign sheet, roll call, RFID-based systems, punch-card systems, swipe card systems, and biometric systems such as fingerprint analysis, iris analysis, and so on are all available for recording attendance in schools or universities. All of these systems have some or all of the following disadvantages: cause disruption to event conduct, high upfront costs, the possibility of proxy and incorrect input, a kiosk can only handle one user at a time, which can cause huge delays when a large number of users want to mark their attendance, especially in colleges and schools. Some more advanced systems have been proposed or are in the experimental stage in recent years that overcome some of the previously described concerns, although they have their downsides. One such system requires students to travel along a certain corridor, which may cause delays when a large number of students seek to indicate their attendance. Most existing solutions are invalid or impracticable for institutions that require attendance to be conducted on a per-time-slot basis. All of these issues are addressed by the proposed solution.





**Proposed System** 

The proposed system processes the video feed of CCTV cameras installed in the classroom to capture face samples of subjects in the CCTV cameras' field of view and feed them to a Facial recognition system based on very popular Python libraries maintained by tech giant Google to perform facial recognition using Deep Learning CNN model pre-trained for face detection and general face recognition and then trained on the dataset consisting of current students and faculties, and then continuously updated and retrained on new admissions of students and faculties every year or as needed, to recognise the subject's identity based on the student and faculty records maintained by the institution they are present at, and mark their attendance based on date, time slot, subject of attendance, and so on. The attendance will be stored in a MySQL based database and can be edited by the faculty up to a limited time and by admin indefinitely. Students and faculty can view their attendance records.



**Working of the Proposed System**

The live video feed from the CCTV cameras installed in the classrooms/lecture halls is sent to an intranet server, where it is first pre-processed, and each detected face is cut out of the frame captured, passed on as individual images, and transformed into a valid input format for the facial recognition model. The model runs facial recognition on each face image and outputs a list of names of people recognised. This list is subsequently passed as an argument in MySQL query, which updates attendance in the institute's relational database. Different views of this Relational database are leveraged to provide different information to different types of end-users on the website. The web platform features three classes of users: admin, faculty, and student. Each has varied access and is shown information based on their class. Admins have complete control and can access and edit all records.


![synopsis_draft_v_3](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.002.png)

## **Outlook**
Design:

This is the initial design and we have tried to complete it as close to the design and is not final. We keep updating the designs as per our needs.

**(\*This does not depict final UI and are subject to change)**

![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.009.png)![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.009.png)![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.009.png)![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.010.png)![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.011.png)![](Aspose.Words.9ac99b99-725b-4f01-b49b-f72bfef4f176.012.png)