# calhacks-transfer-app
App to help community college students figure out their course plan, regardless of where they want to go.

Utilizing:
- MindsDB for data storage & preliminary data clean up with AI
- together.ai for AI data processing on the user's end
- ??? for frontend

---
Idea

Background: John is a CS student at De Anza College (a community college), who wishes to transfer to a university in the future. he's a very ambitious student, and wishes to go to either a UC, an Ivy League college, or MIT.

Since John is studying at a California Community College, figuring out his plan for the UCs is easy! He just has to go on assist.org, enter his college and select one of the UCs, enter his major, download the articulation agreement, copy down the classes that the articulation agreement tells him to take, and repeat this whole process all over again for each UC campus. How easy!

For Ivy League and MIT, it's even easier! He just has to dig through countless Google searches to eventually find a page from a specific college, denoting what they're generally looking for in transfer applicants, then compare their criteria to the different classes his college offers, then repeat again for the next college.

There is an easier way to do this. Enter [PLACEHOLDER NAME].

With [PLACEHOLDER NAME], it can:
- automatically analyze the assist.org articulation agreement for multiple colleges
- provide students with an easy way to figure out the transfer requirements/criteria of out-of-state/private colleges
- merge all of the information it has into one simple and easy to read page, with Generative AI being able to further clean up the information to make it more human-digestable.

---
Data Handling for Individual Universities

DB Structure:

__classes_requirements (each row is a class requirement)__  
uni_name - University Name - For convenience's sake  
uni_id - University ID - We either generate this ourselves or we borrow from assist.org whenever possible  
data_type - Source of the Data - e.g. "california_assist", "private_scraped", "public_scraped"  
major - Major this data point is for - Can be specific (e.g. "Computer Science") or general if it applies to all majors (GE reqs)  
class_code - A specific class needed by the school - Needs to be the specific course code required by the school  
class_name - Name of the class

[TODO] Add a row for AI to process

__california_assist (each row is a class equivalency between two schools)__  
sending_name - Sender College Name  
sending_id - Sender College ID  
receive_name - Receiving College Name  
receive_id - Receiving College ID  
sending_course_code - Sender College Class Code  
sending_course_name - Sender College Class Name  
receiving_course_code - Receiving College Class Code  
receiving_course_name - Receiving College Class Name  
