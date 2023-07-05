from pystructurizr.dsl import Workspace

# Create the model(s)
workspace = Workspace()
user = workspace.Model("Users").Person("City of Seattle")
software_system = workspace.Model("System").SoftwareSystem("Software System")
webapp = software_system.Container("Web Application: FastAPI")
db = software_system.Container("Database: Azure PostgreSQL")

# Define the relationships
user.uses(webapp, "Uses")
webapp.uses(db, "Reads from and writes to")

# Create a view onto the model
workspace.ContainerView(
    software_system, 
    "My Container View",
    "The container view of our simply software system."
)
