const API = "http://127.0.0.1:12345";
const token = sessionStorage.getItem("access_token");

const usersContainer = document.getElementById("users-container");
const groupsContainer = document.getElementById("groups-container");
const projectsContainer = document.getElementById("projects-container");
const adminMessage = document.getElementById("admin-message");


function buildElement(tagName, cssClass, TEXT_VALUE)
{
    const element = document.createElement(tagName);

    if(cssClass)
    {
        element.className = cssClass;
    }

    if(TEXT_VALUE !== undefined && TEXT_VALUE !== null)
    {
        element.textContent = String(TEXT_VALUE)
    }

    return element;
}

async function api(path, method = "GET", body=null)
{
    const response = await fetch(`${API}${path}`, {
        method: method,
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: body ? JSON.stringify(body) : null
    });

    const data = await response.json();

    //console.log("Backend Error Response: ", data);  

    if(response.status === 401 || response.status === 403)
    {
        if(data.detail === "Invalid or Expired token")
        {    
            sessionStorage.removeItem("access_token");
            window.location.replace("index.html");
            return;
        }
    }

    if(!response.ok)
    {
        //console.log("API Error:", response.status, data);

        const error = new Error(data.detail || "Something went wrong");
        error.status = response.status
        throw error;
    }

    return data;
}

async function loadUsers()
{
    try
    {
        const users = await api("/admin/users");

        usersContainer.innerHTML = "";

        if(users.length === 0)
        {
            usersContainer.textContent = "No users found";
            return;
        }

        users.forEach(user => {
            const userCard = buildElement("div", "user-item");

            const username = buildElement("h3", null, user.username);
            const userId = buildElement("p", null, `User Id: ${user.id}`);
            const role = buildElement("p", null, `Role: ${user.role}`);
            const status = buildElement("p", null, `Status: ${user.account_status}`);

            const statusSelect = buildElement("select", "status-select");

            ["active", "suspended", "deactivated"].forEach(accountStatus => {
                const option = buildElement("option", null, accountStatus);
                option.value = accountStatus;

                if(accountStatus === user.account_status)
                {
                    option.selected = true;
                }

                statusSelect.appendChild(option);
            });

            const updateButton = buildElement("button", null, "Update Status");

            updateButton.addEventListener("click", async () => {
                try
                {
                    await api(`/admin/${user.id}/status`, "PUT", {
                        account_status: statusSelect.value
                    });

                    adminMessage.textContent = "Account status updated successfully";

                    loadUsers();
                }
                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            const deleteButton = buildElement("button", null, "Delete User");

            deleteButton.addEventListener("click", async () =>{
                const confirmDelete = confirm(`Are you sure you want to delete ${user.username} ?`);

                if(!confirmDelete)
                {
                    return;
                }

                try
                {
                    const result = await api(`/admin/delete/user/${user.id}`, "DELETE");
                    adminMessage.textContent = result.message;
                    loadUsers();
                }
                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            userCard.append(username, userId, role, status, statusSelect, updateButton);

            if(user.role !== "admin")
            {
                userCard.appendChild(deleteButton);
            }

            usersContainer.appendChild(userCard);
        });
    }

    catch(error)
    {
        if(error.status === 401 || error.status === 403)
        {
            window.location.replace("index.html");
            return;
        }
        adminMessage.textContent = error.message;
    }
}

async function loadGroups()
{
    try
    {
        const groups = await api("/admin/groups");
        console.log(groups[0]);

        groupsContainer.innerHTML = "";

        if(groups.length === 0)
        {
            groupsContainer.textContent = "No groups found";
            return;
        }

        groups.forEach(group => {
            const groupCard = buildElement("div", "group-item");

            const groupName = buildElement("h3", null, group.name);
            const groupId = buildElement("p", null, `Group Id: ${group.id}`);
            const description = buildElement("p", null, `Description: ${group.description}`);
            const manager = buildElement("p", null, `Manager Id: ${group.manager_id}`);
            const owner = buildElement("p", null, `Owner Id: ${group.owner_id}`);

            const techLeadInput = buildElement("input", null);
            techLeadInput.type = "number";
            techLeadInput.min = "1";
            techLeadInput.placeholder = "Tech Lead User ID";

            const assignTechLeadButton = buildElement("button", null, "Assign Tech Lead");

            assignTechLeadButton.addEventListener("click", async () => {
                const techLead = Number(techLeadInput.value);

                if(!techLead || techLead < 1)
                {
                    adminMessage.textContent = "Enter a valid User Id";
                    return;
                }

                try
                {
                    await api(`/admin/groups/${group.id}/tech-leads`, "POST", {
                        tech_lead_id : techLead
                    });

                    adminMessage.textContent = "Tech Lead assigned successfully";

                    loadGroups();
                }

                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            const developerInput = buildElement("input", null);
            developerInput.type = "number";
            developerInput.min = "1";
            developerInput.placeholder = "Developer User Id";

            const assignDeveloperButton = buildElement("button", null, "Assign Developer");

            assignDeveloperButton.addEventListener("click", async () => {
                const developerId = Number(developerInput.value);

                if(!developerId || developerId < 1)
                {
                    adminMessage.textContent = "Enter a valid User Id";
                    return;
                }

                try
                {
                    await api(`/admin/groups/${group.id}/developers`, "POST", {
                        dev_id: developerId
                    });

                    adminMessage.textContent = "Developer Assigned Successfully";
                    
                    loadGroups();
                }

                catch(error)
                {
                    adminMessage.textContent = error.message;
                }

            });

            groupCard.append(groupName, groupId, description, manager, owner, techLeadInput, assignTechLeadButton, developerInput, assignDeveloperButton);

            groupsContainer.appendChild(groupCard);
        })
    }

    catch(error)
    {
        if(error.status === 401 || error.status === 403)
        {
            window.location.replace("index.html");
            return;
        }
        adminMessage.textContent = error.message;
    }

}

const createGroupForm = document.getElementById("create-group-form");

createGroupForm.addEventListener("submit", async (event) =>{
    event.preventDefault();

    const groupData = {
        name: document.getElementById("group-name").value,
        description: document.getElementById("group-description").value,
        manager_id: Number(document.getElementById("manager-id").value)
    };

    try
    {
        const result = await api("/admin/groups", "POST", groupData);

        adminMessage.textContent = result.message || "Group Created Successfully";

        createGroupForm.reset();
        loadGroups();
    }
    catch(error)
    {
        adminMessage.textContent = error.message;
    }

});

async function loadProjects()
{
    try
    {
        const projects = await api("/admin/projects");
        //console.log(projects);

        projectsContainer.innerHTML = "";

        if(projects.length === 0)
        {
            projectsContainer.textContent = "No Projects Found";
            return;
        }

        projects.forEach(project => {
            const projectCard = buildElement("div", "project-item");

            const projectName = buildElement("h3", null, project.name);
            const projectId = buildElement("p", null, `Project Id: ${project.id}`);
            const description = buildElement("p", null, `Description: ${project.description}`);
            const owner = buildElement("p", null, `Owner: ${project.owner_id}`);
            const group = buildElement("p", null, `Group Id: ${project.group_id}`);
            const status = buildElement("p", null, `Status: ${project.status}`);

            const groupInput = buildElement("input", null);
            groupInput.type = "number";
            groupInput.min = "1";
            groupInput.placeholder = "Group Id";

            const assignGroupButton = buildElement("button", null, "Assign Button");

            assignGroupButton.addEventListener("click", async () => {
                const groupId = Number(groupInput.value);

                if(!groupId || groupId < 1)
                {
                    adminMessage.textContent = "Enter a valid Group Id";
                    return;
                }

                try
                {
                    const result = await api(`/admin/projects/${project.id}/group`, "PATCH", {
                        group_id: groupId
                    });

                    adminMessage.textContent = result.message || "Project assign to group successfully";
                    
                    loadProjects();
                }

                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            const editName = buildElement("input", null);
            editName.type = "text";
            editName.value = project.name;

            const editDescription = buildElement("input", null);
            editDescription.type = "text";
            editDescription.value = project.description;

            const updateButton = buildElement("button", null, "Update Project");

            updateButton.addEventListener("click", async () => {
                
                const projectData = {
                    name: editName.value,
                    description: editDescription.value
                };

                try
                {
                    const result = await api(`/projects/${project.id}`, "PUT", projectData);

                    adminMessage.textContent = result.message || "Project updated successfully";

                    loadProjects();
                }

                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            const archiveButton = buildElement("button", null, "Archive Project");

            archiveButton.addEventListener("click", async () => {
                try
                {
                    const result = await api(`/projects/${project.id}/archive`, "PATCH");

                    adminMessage.textContent = result.message || "Project archived successfully";

                    loadProjects();
                }
                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            const restoreButton = buildElement("button", null, "Restore Project");

            restoreButton.addEventListener("click", async () => {

                try
                {
                    const result = await api(`/projects/${project.id}/restore`, "PATCH");

                    adminMessage.textContent = result.message || "Project Restored Successfully";

                    loadProjects();
                }

                catch(error)
                {
                    adminMessage.textContent = error.message;
                }
            });

            projectCard.append(
                projectName,
                projectId,
                description,
                owner,
                group,
                status,
                groupInput,
                assignGroupButton,
                editName,
                editDescription,
                updateButton,
                archiveButton,
                restoreButton
            );

            projectsContainer.appendChild(projectCard);
        });
    }

    catch(error)
    {
        if(error.status === 401 || error.status === 403)
        {
            window.location.href = "index.html";
            return;
        }
        adminMessage.textContent = error.message;
    }
}

const createProjectForm = document.getElementById("create-project-form");

createProjectForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const projectData = {
        name: document.getElementById("project-name").value,
        description: document.getElementById("project-description").value
    };

    try
    {
        const result = await api("/projects", "POST", projectData);

        adminMessage.textContent = result.message || "Project Created Successfully";

        createProjectForm.reset();
        loadProjects();
    }

    catch(error)
    {
        adminMessage.textContent = error.message;
    }
})

if(!token)
{
    window.location.replace("index.html");
}

else
{
    loadUsers();
    loadGroups();
    loadProjects();
}