"""The two estates the generator builds (D-30, seed-reuse-notes.md §5.7).

Each estate is a staff directory and a list of products. A product spec gives its seat count,
its unit price (None where the contract states none), the share of seats nobody holds, and
how the people holding the others behave: the share whose use has stopped or never started
("idle") and the share who use it now and then ("occasional"); the rest use it regularly.
Classes are never set here: the generator derives them from the seats it makes, by music.md's
rules. Who has left comes from the directory, so one leaver's seats are Leaver on every product.

Names follow Seed v0.1's style: realistic software products. The figures are SeedFactory's own
and Seed v0.1's are not targets (§5.5).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProductSpec:
    name: str
    vendor: str
    seats: int
    unit_cost: int | None
    unassigned: float
    idle: float
    occasional: float
    departments: dict[str, float] = field(default_factory=dict)  # empty: the estate's headcount weights


@dataclass(frozen=True)
class EstateSpec:
    name: str
    title: str
    description: str
    people: int
    leaver_rate: float
    joiner_rate: float
    departments: dict[str, float]  # headcount weights
    products: tuple[ProductSpec, ...]


# The sample's account (environment.md, Adaptation Layer): a professional services firm,
# departments named as the firm names them, spend in US dollars.
PRIMARY = EstateSpec(
    name="primary",
    title="Primary estate",
    description="A professional services firm working in several countries",
    people=5000,
    leaver_rate=0.035,
    joiner_rate=0.1,
    departments={
        "Consulting": 40,
        "Engineering": 12,
        "Finance": 8,
        "Legal": 6,
        "Marketing": 7,
        "Operations": 10,
        "People": 5,
        "Sales": 12,
    },
    products=(
        ProductSpec("Microsoft 365 E3", "Microsoft", 4200, 36, 0.03, 0.05, 0.08),
        ProductSpec("Microsoft 365 E5", "Microsoft", 900, 57, 0.05, 0.10, 0.15),
        ProductSpec("Power BI Pro", "Microsoft", 800, 14, 0.06, 0.20, 0.25, {"Consulting": 50, "Finance": 25, "Operations": 15, "Sales": 10}),
        ProductSpec("Visio Plan 2", "Microsoft", 420, None, 0.09, 0.30, 0.28),
        ProductSpec("Project Plan 3", "Microsoft", 360, 30, 0.11, 0.26, 0.25, {"Consulting": 60, "Operations": 25, "Engineering": 15}),
        ProductSpec("Acrobat Pro", "Adobe", 1200, 20, 0.04, 0.12, 0.30),
        ProductSpec("Creative Cloud All Apps", "Adobe", 240, 90, 0.07, 0.15, 0.18, {"Marketing": 80, "Sales": 10, "Consulting": 10}),
        ProductSpec("Sales Cloud Enterprise", "Salesforce", 620, 165, 0.05, 0.10, 0.12, {"Sales": 80, "Marketing": 10, "Consulting": 10}),
        ProductSpec("Tableau Creator", "Salesforce", 180, 75, 0.08, 0.22, 0.25, {"Consulting": 50, "Finance": 30, "Operations": 20}),
        ProductSpec("Jira Software", "Atlassian", 800, None, 0.04, 0.08, 0.12, {"Engineering": 60, "Consulting": 30, "Operations": 10}),
        ProductSpec("Confluence", "Atlassian", 900, 6, 0.03, 0.10, 0.30, {"Engineering": 45, "Consulting": 40, "Operations": 15}),
        ProductSpec("Zoom Workplace Business", "Zoom", 900, 18, 0.05, 0.15, 0.30),
        ProductSpec("DocuSign eSignature", "DocuSign", 310, 40, 0.06, 0.18, 0.35, {"Legal": 40, "Sales": 30, "Finance": 20, "People": 10}),
        ProductSpec("AutoCAD LT", "Autodesk", 140, None, 0.10, 0.20, 0.15, {"Engineering": 80, "Operations": 20}),
        ProductSpec("Miro Business", "Miro", 520, None, 0.12, 0.28, 0.30, {"Consulting": 60, "Marketing": 20, "Engineering": 20}),
        ProductSpec("Westlaw Edge", "Thomson Reuters", 260, None, 0.05, 0.08, 0.10, {"Legal": 90, "Consulting": 10}),
        ProductSpec("Smartsheet Business", "Smartsheet", 300, 25, 0.10, 0.25, 0.25, {"Operations": 50, "Consulting": 40, "Finance": 10}),
    ),
)

# The data-swap estate (T-08, FR-T-2): the same schema and methodology, a different estate.
# Other vendors, products, sizes and departments; none of the primary's names.
ALTERNATE = EstateSpec(
    name="alternate",
    title="Alternate estate",
    description="A software company",
    people=1500,
    leaver_rate=0.05,
    joiner_rate=0.15,
    departments={
        "Platform": 30,
        "Product": 20,
        "Design": 8,
        "Data": 10,
        "Support": 15,
        "Finance": 7,
        "People": 10,
    },
    products=(
        ProductSpec("Google Workspace Business Standard", "Google", 1400, 14, 0.04, 0.06, 0.10),
        ProductSpec("GitHub Enterprise", "GitHub", 520, 21, 0.05, 0.10, 0.12, {"Platform": 60, "Data": 25, "Product": 15}),
        ProductSpec("GitHub Copilot Business", "GitHub", 480, 19, 0.08, 0.20, 0.25, {"Platform": 65, "Data": 25, "Product": 10}),
        ProductSpec("IntelliJ IDEA Ultimate", "JetBrains", 260, 50, 0.06, 0.15, 0.20, {"Platform": 75, "Data": 25}),
        ProductSpec("ReSharper", "JetBrains", 90, None, 0.10, 0.30, 0.25, {"Platform": 100}),
        ProductSpec("Figma Professional", "Figma", 140, 15, 0.07, 0.12, 0.20, {"Design": 70, "Product": 30}),
        ProductSpec("FigJam", "Figma", 220, None, 0.12, 0.30, 0.30, {"Design": 30, "Product": 40, "Platform": 30}),
        ProductSpec("Notion Plus", "Notion", 600, 10, 0.06, 0.18, 0.30),
        ProductSpec("1Password Business", "1Password", 1350, 8, 0.03, 0.05, 0.10),
        ProductSpec("Loom Business", "Loom", 300, None, 0.10, 0.35, 0.30, {"Support": 40, "Product": 30, "Design": 30}),
        ProductSpec("Asana Advanced", "Asana", 260, 25, 0.09, 0.22, 0.25, {"Product": 50, "Support": 30, "People": 20}),
    ),
)

ESTATES = {spec.name: spec for spec in (PRIMARY, ALTERNATE)}

FIRST_NAMES = (
    "Aisha", "Alejandro", "Amara", "Ananya", "Andrei", "Anna", "Arjun", "Ben", "Bianca", "Carlos",
    "Chen", "Chloe", "Daniel", "Dmitri", "Elena", "Emeka", "Emily", "Fatima", "Felix", "Grace",
    "Hana", "Hassan", "Ines", "Isaac", "Jamal", "James", "Javier", "Jia", "Jonas", "Julia",
    "Kai", "Kemi", "Kenji", "Laila", "Lars", "Leah", "Lucas", "Mai", "Marco", "Maria",
    "Mateo", "Maya", "Mei", "Mohammed", "Nadia", "Naomi", "Nikhil", "Noah", "Olga", "Omar",
    "Oscar", "Paulo", "Priya", "Rafael", "Rahul", "Rania", "Rosa", "Ruth", "Samir", "Sara",
    "Sean", "Sofia", "Sunita", "Tariq", "Thandiwe", "Thomas", "Tomas", "Valentina", "Victor", "Wei",
    "Yara", "Yusuf", "Zara", "Zoe", "Ahmed", "Beatriz", "Connor", "Divya", "Erik", "Freya",
)

LAST_NAMES = (
    "Abebe", "Adeyemi", "Ali", "Alvarez", "Andersen", "Bakker", "Banerjee", "Becker", "Bianchi", "Brown",
    "Campbell", "Chen", "Costa", "Das", "Dubois", "Edwards", "Eriksson", "Fernandes", "Fischer", "Garcia",
    "Gupta", "Haddad", "Hansen", "Hughes", "Ibrahim", "Ivanova", "Jansen", "Jones", "Kaur", "Khan",
    "Kim", "Kowalski", "Kumar", "Larsen", "Lee", "Lopez", "Martin", "Mehta", "Mendes", "Moreau",
    "Murphy", "Nakamura", "Nguyen", "Novak", "Okafor", "Olsen", "Patel", "Pereira", "Petrov", "Quinn",
    "Rahman", "Reyes", "Rossi", "Santos", "Sato", "Schmidt", "Shah", "Silva", "Singh", "Smith",
    "Sousa", "Suzuki", "Tanaka", "Taylor", "Thompson", "Torres", "Van Dijk", "Varga", "Walker", "Wang",
    "Weber", "Williams", "Wilson", "Wong", "Yamamoto", "Yilmaz", "Young", "Zhang", "Zhou", "Okoro",
)
