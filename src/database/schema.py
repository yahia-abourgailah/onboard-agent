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


class Departments(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str
    head: str


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
DEPARTMENTS = [
    {
        "name": "Marketing",
        "description": "Responsible for developing and executing marketing strategies, managing the company's brand, running campaigns, creating content, conducting market research, and supporting business growth through customer engagement.",
        "head": "Rana Ashraf",
    },
    {
        "name": "Sales Operations",
        "description": "Supports the sales organization by optimizing sales processes, managing CRM systems, generating reports, analyzing sales performance, and improving operational efficiency.",
        "head": "Rania Salama",
    },
    {
        "name": "Sales",
        "description": "Responsible for acquiring new customers, managing client relationships, achieving sales targets, negotiating contracts, and driving company revenue.",
        "head": """Second floor: Diana Griece, Shenawy + Mairam Wahba, Mahmoud Alaa, Mostafa Fathy, Lahseen + Assaf, Ammar + Gehad, Seif El Ramly
          | Third floor: Abo El Fadl, Shimmy
          | Fourth floor: Hossam Abdelrahman, Hady El Rady, Salma + Omar, Sameh + Ziad, Merna + Salah
          | Fifth floor: no current head
          | Sixth floor: Manosur + Metawa, Nasser + Shaker""",
    },
    {
        "name": "Technology",
        "description": "Designs, develops, and maintains the company's software products and technical infrastructure. Includes frontend, backend, mobile, AI/ML, UI/UX, QA, and DevOps teams.",
        "head": "Mohamed Reda",
    },
    {
        "name": "IT",
        "description": "Maintains the organization's internal IT infrastructure, provides technical support, manages hardware and software, ensures network availability, and enforces cybersecurity practices.",
        "head": "Mohamed Halawa",
    },
    {
        "name": "Business Relations",
        "description": "Builds and maintains strategic partnerships with clients and stakeholders, manages key accounts, and identifies opportunities for collaboration and business expansion.",
        "head": "Mohamed Ibrahim",
    },
    {
        "name": "Business Development",
        "description": "Identifies new business opportunities, develops growth strategies, explores new markets, builds strategic partnerships, and supports long-term company expansion.",
        "head": "Ehab Ali",
    },
    {
        "name": "Finance",
        "description": "Manages the company's financial planning, budgeting, accounting, payroll, reporting, accounts payable and receivable, compliance, and financial analysis.",
        "head": "Maii Adel",
    },
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


DEPARTMENTS_SCHEMA = """
Table: departments
Description: Contains information about each department in the company, including its purpose and department head.

Columns:
- id (integer, primary key): Unique identifier for the department.
- name (string): Name of the department (e.g. "Technology", "Finance", "Marketing").
- description (string): Brief overview of the department's responsibilities and functions.
- head (string): Name of the department head (Sales have many heads for different franchises).

Use this table to answer questions like:
- "What does the Finance department do?"
- "Who is the head of the Technology department?"
- "Tell me about the Business Development department."
- "Which department is responsible for internal IT support?"
- "What are the responsibilities of Sales Operations?"
- "Where do I go for HR inquiries?"
"""
