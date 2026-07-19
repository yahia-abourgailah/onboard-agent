from sqlmodel import Field, SQLModel


class Departments_Per_Floor(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    floor: str
    departments_and_facilities: str


class Mentors_For_Interns(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    position: str
    department: str


DEPARTMENTS_PER_FLOOR = [
    {"floor": "B2", "departments_and_facilities": "Parking"},
    {"floor": "B1", "departments_and_facilities": "Parking, Prayer room (masjid) and toilet"},
    {
        "floor": "Ground",
        "departments_and_facilities": "7 interview rooms (outside the building), Outdoors shared area, Dancing Goat for Coffee, CEO and board offices, Non-sales, Marketing, Corporate Services and Sales Operations, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "First",
        "departments_and_facilities": "Silence Pods,CTO/CHRO/CFO offices, HR, Business Relations, Finance, Tech, IT and Business Development, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "Second",
        "departments_and_facilities": "Sales, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "Third",
        "departments_and_facilities": "Sales, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "Fourth",
        "departments_and_facilities": "Sales, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "Fifth",
        "departments_and_facilities": "Sales, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
    {
        "floor": "Sixth",
        "departments_and_facilities": "Sales, Toilets, Kitchen, Coffee Machine, Water Dispenser, Back Area (Break Area) and Meeting Rooms",
    },
]

MENTORS_FOR_INTERNS = [
    {
        "name": "Amira Habib",
        "position": "Talent Acquisition Team Leader",
        "department": "Human Resources",
    },
    {
        "name": "Hussam Badawy",
        "position": "Senior Learning & Development Specialist",
        "department": "Human Resources",
    },
    {
        "name": "Laila Mourad",
        "position": "Marketing Supervisor",
        "department": "Commercial & Strategy",
    },
    {
        "name": "Shahd Ayman",
        "position": "Senior HR Operations Specialist",
        "department": "Human Resources",
    },
    {
        "name": "Karim Elmaadawy",
        "position": "Senior Account Manager",
        "department": "Business Relations",
    },
    {"name": "Ahmed Hossam", "position": "Collection Manager", "department": "Finance"},
    {"name": "Eslam Ashraf", "position": "Accounts Payable Section Head", "department": "Finance"},
    {"name": "Mohamed Elmedany", "position": "UI/UX Team Leader", "department": "Technology"},
    {"name": "Mohamed Adel", "position": "Senior Frontend Developer I", "department": "Technology"},
    {
        "name": "Mostafa Younis",
        "position": "Senior Mobile Application Developer I",
        "department": "Technology",
    },
    {"name": "Omar Derbala", "position": "Backend Developer", "department": "Technology"},
    {"name": "Yahia Abourgailah", "position": "ML/AI Engineer", "department": "Technology"},
]

DEPARTMENTS_PER_FLOOR_SCHEMA = """
Table: departments_per_floor
Description: Maps each floor of the office building to the departments and facilities located on it.

Columns:
- id (integer, primary key): Unique identifier for the row.
- floor (string): Name of the floor (e.g. "B2", "B1", "Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth").
- departments_and_facilities (string): Comma-separated list of departments and/or facilities located on that floor (e.g. "Sales, Toilets, Kitchen, Coffee Machine").

Use this table to answer questions like:
- "Which floor is the Sales department on?"
- "What facilities are available on the Ground floor?"
- "Where can I find a prayer room?"
"""
MENTORS_FOR_INTERNS_SCHEMA = """
Table: mentors_for_interns
Description: Lists mentors available to interns, along with their job position and department.

Columns:
- id (integer, primary key): Unique identifier for the row.
- name (string): Full name of the mentor (e.g. "Amira Habib").
- position (string): Job title of the mentor (e.g. "Senior Frontend Developer I").
- department (string): Department the mentor belongs to (e.g. "Human Resources", "Technology", "Finance").

Use this table to answer questions like:
- "Who can mentor me in the Technology department?"
- "Who is the mentor with the position 'Marketing Supervisor'?"
- "List all mentors in Human Resources."
"""
