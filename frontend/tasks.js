const API_BASE_URL = "http://127.0.0.1:12345";

// Page Elements
const backToDashboardButton = document.getElementById("back-to-dashboard");
const taskListSelection = document.getElementById("task-list-section");
const createTaskSection = document.getElementById("create-task-section");
const assignTaskSection = document.getElementById("assign-task-section")

// Current user's account information
let currentAccount = null;


// Navigate back to the main dashboard
// sessionStorage is preserved when navigating within the same tab
backToDashboardButton.addEventListener("click", function(){
    window.location.href = "index.html";
})

// Display a message safely
function showMessage(container, message, isError = false)
{
    let messageElement = container.querySelector(".task-message");

    if(!messageElement)
    {
        messageElement = document.createElement("p");
        messageElement.className = "task-message";
        messageElement.setAttribute("role", "status");
        container.appendChild(messageElement);
    }

    messageElement.textContent = message;
    messageElement.style.color = isError ? "crimson": "inherit";
}

// Make authenticated API requests.
async function apiRequest(endpoint, options = {})
{
    const token = sessionStorage.getItem("access_token");

    if(!token)
    {
        window.location.href = "index.html";
        throw new Error("Your session has expired. Please log in again.");
    }

    const headers = {
        Authorization: `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });


    let data = {};

    try
    {
        data = await response.json();
    }

    catch
    {
        
    }

    if(response.status === 401)
    {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("username");

        window.location.href = "index.html";
        throw new Error("Your Session has expired. Please Log in again");
    }

    if(!response.ok)
    {
        const detail = Array.isArray(data.detail)
        ? data.detail.map(item => item.msg || String(item)).join(", ")
        : data.detail;


        throw new Error(detail || data.message || `Request failed (${response.status}).`);
    }

    return data;
}

// Build HTML elements using textContent to avoid inserting API data as HTML
function buildElement(tagName, cssClass, TEXT_VALUE)
{
    const element = document.createElement(tagName);

    if(cssClass)
    {
        element.className = cssClass;
    }

    if(TEXT_VALUE !== undefined && TEXT_VALUE !== null)
    {
        element.textContent = String(TEXT_VALUE);
    }

    return element;
}

// Clear section while preserving its heading
function clearSection(section, headingSelector)
{
    const heading = section.querySelector(headingSelector);

    section.replaceChildren();

    if(heading)
    {
        section.appendChild(heading);
    }
}


// Normalize task-list responses from the existing backend
function extractTasks(data)
{
    if(Array.isArray(data))
    {
        return data;
    }

    if(Array.isArray(data.Tasks))
    {
        return data.Tasks;
    }

    if(Array.isArray(data.detail))
    {
        return data.detail;
    }

    return [];
}

// Render Individual Task
function renderTasks(tasks)
{
    clearSection(taskListSelection, "h3");

    const heading = taskListSelection.querySelector("h3");

    if(heading)
    {
        heading.textContent = currentAccount.role === "developer" ? "My Assigned Tasks" : "Project Tasks";
    }

    if(tasks.length === 0)
    {
        showMessage(taskListSelection, "No tasks to display yet.");
        return;
    }

    const taskContainer = buildElement("div", "task-list");

    tasks.forEach(task => {
        const card = buildElement("article", "task-card");

        card.appendChild(
            buildElement("h4", "task-title", task.title || "Untitled task")
        );

        if(task.description)
        {
            card.appendChild(buildElement("p", "task-description", task.description));
        }

        const details = buildElement("div", "task-details");

        details.appendChild(
            buildElement("p", "task-id", `Task ID: ${task.id ?? "N/A"}`)
        );

        details.appendChild(
            buildElement("p", "task-project", `Project ID: ${task.project_id ?? "N/A"}`)
        );

        details.appendChild(
            buildElement("p", "task-status", `Status: ${task.status || "Unknown"}`)
        );

        details.appendChild(
            buildElement("p", "task-priority", `Priority: ${task.priority || "Unknown"}`)
        );

        details.appendChild(
            buildElement("p", "task-assignee", `Assigned To: ${task.assigned_to ?? "Unassigned"}`)
        );

        card.appendChild(details);


        // Status Controls - Tech Leads only
        if(currentAccount.role === "tech lead")
        {
            const statusSelect = buildElement("select", "task-status-select");

            const statuses = ["created", "assigned", "in_progress", "on_hold", "completed", "cancelled"];

            statuses.forEach(function(status) {
                const option = buildElement("option", "", status.replace("_", " ").toUpperCase());

                option.value = status;
                statusSelect.appendChild(option);
            });

            statusSelect.value = task.status;

            card.appendChild(statusSelect);

            const updateStatusButton = buildElement("button", "", "Update Status");

            updateStatusButton.type = "button";

            card.appendChild(updateStatusButton);

            updateStatusButton.addEventListener("click", async function() {
                try {
                    const data = await apiRequest(`/tasks/${task.id}/status`, {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({status: statusSelect.value})
                    });

                    await loadTasks();
                    showMessage(taskListSelection, data.message);
                }

                catch(error){
                    showMessage(taskListSelection, error.message, true);
                }
            });
        }

        // Priority Controls - Tech Leads only
        if(currentAccount.role === "tech lead")
        {
            const prioritySelect = buildElement("select", "task-priority-select");

            const priorities = ["critical", "high", "medium", "low"];

            priorities.forEach(function(priority) {
                const option = buildElement("option", "", priority.charAt(0).toUpperCase() + priority.slice(1));

                option.value = priority;
                prioritySelect.appendChild(option);
            });

            prioritySelect.value = task.priority;

            const updatePriorityButton = buildElement("button", "", "Update Priority");
            updatePriorityButton.type = "button";

            updatePriorityButton.addEventListener("click", async function(){
                try{
                    const data = await apiRequest(`/tasks/${task.id}/priority`, {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            priority: prioritySelect.value
                        })
                    });

                    await loadTasks();
                    showMessage(taskListSelection, data.message)
                }
                
                catch(error){
                    showMessage(taskListSelection, error.message, true);
                }
            });
            card.appendChild(prioritySelect);
            card.appendChild(updatePriorityButton);
        }

        taskContainer.appendChild(card);
    });

    taskListSelection.appendChild(taskContainer);

}

// Load Tasks
async function loadTasks()
{
    clearSection(taskListSelection, "h3");
    showMessage(taskListSelection, "Loading tasks....");

    try
    {
        let data;

        if(currentAccount.role === "manager" || currentAccount.role === "tech lead")
        {
            if(currentAccount.group_id == null)
            {
                showMessage(taskListSelection, "Your account is not assigned to any group", true);
                return;
            }

            data = await apiRequest(`/groups/${currentAccount.group_id}/tasks`);
        }

        else if(currentAccount.role === "developer")
        {
            if(currentAccount.group_id == null)
            {
                showMessage(taskListSelection, "Your account is not assigned to a group", true);
                return;
            }
            data = await apiRequest("/users/me/tasks");
        }

        else
        {
            showMessage(taskListSelection, "A task-list endpoint is not currently available for your role");
            return;
        }

        renderTasks(extractTasks(data));
    }

    catch(error)
    {
        showMessage(taskListSelection, error.message, true);
    }
}

// Build the task-creation form for the tech leads only.
function renderCreateTaskForm()
{
    clearSection(createTaskSection, "h3");

    if(currentAccount.role !== "tech lead")
    {
        showMessage(createTaskSection, "Task creation is available to tech leads only.");
        return;
    }

    if(currentAccount.group_id == null)
    {
        showMessage(createTaskSection, "You must belong to a group before creating task.", true);
        return;
    }

    const Form = buildElement("form", "create-task-form");

    const projectLabel = buildElement("label", "", "Project Id");
    projectLabel.htmlFor = "task-project-id";

    const projectInput = buildElement("input");
    projectInput.id = "task-project-id";
    projectInput.name = "project_id";
    projectInput.type = "number";
    projectInput.min = "1";
    projectInput.step = "1";
    projectInput.required = true;

    const titleLabel = buildElement("label", "", "Task Title");
    titleLabel.htmlFor = "task-title";

    const titleInput = buildElement("input");
    titleInput.id = "task-title";
    titleInput.name = "title";
    titleInput.type = "text";
    titleInput.maxLength = 200;
    titleInput.required = true;

    const descriptionLabel = buildElement("label", "", "Description");
    descriptionLabel.htmlFor = "task-description";

    const descriptionInput = buildElement("textarea");
    descriptionInput.id = "task-description";
    descriptionInput.name = "description";
    descriptionInput.rows = 4;
    descriptionInput.required = true;


    const submitButton = buildElement("button", "",  "Create Task");
    submitButton.type = "submit";

    Form.append(
        projectLabel,
        projectInput,
        titleLabel,
        titleInput,
        descriptionLabel,
        descriptionInput,
        submitButton
    );

    Form.addEventListener("submit", async function(event){
        event.preventDefault();

        const ProjectId = Number(projectInput.value);
        const title = titleInput.value;
        const description = descriptionInput.value.trim();

        if(!Number.isSafeInteger(ProjectId) || ProjectId < 1 || !title || !description)
        {
            showMessage(createTaskSection, "Enter a valid project ID, title and description", true);
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Creating....";

        try
        {
            const data = await apiRequest(`/groups/${currentAccount.group_id}/tasks`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        project_id: ProjectId,
                        title: title,
                        description: description
                    })
                }
            );

            showMessage(createTaskSection, "Task created successfully");

            Form.reset();
            await loadTasks();
        }

        catch(error)
        {
            showMessage(createTaskSection, error.message, true);
        }

        finally
        {
            submitButton.disabled = false;
            submitButton.textContent = "Create Task";
        }

    });

    createTaskSection.appendChild(Form);
}

// Build the task-assignment form for tech leads only.
async function renderAssignTaskForm()
{

    clearSection(assignTaskSection, "h3");

        if(currentAccount.role != "tech lead")
        {
            return;
        }

        if(currentAccount.group_id == null)
        {
            showMessage(assignTaskSection, "You must belong to a group before assigning tasks.", true);
            return;
        }

        const form  = buildElement("form", "assign-task-form");

        // Task ID
        const taskLabel = buildElement("label", "", "Task ID");
        taskLabel.htmlFor = "assign-task-id";

        const taskInput = buildElement("input");
        taskInput.id = "assign-task-id";
        taskInput.type = "number";
        taskInput.min = "1";
        taskInput.required = true;

        // Developer selection
        const developerLabel = buildElement("label", "", "Select Developer");
        developerLabel.htmlFor = "assign-developer";

        const developerSelect = buildElement("select");
        developerSelect.id = "assign-developer";
        developerSelect.required = true;

        const defaultOption = buildElement("option", "", "Select a developer");
        defaultOption.value = "";

        developerSelect.appendChild(defaultOption);

        // Add submit button
        const submitButton = buildElement("button","", "Assign Task");
        submitButton.type = "submit";

        form.append(
            taskLabel,
            taskInput,
            developerLabel,
            developerSelect,
            submitButton
        );

        assignTaskSection.appendChild(form);

        try{
            const data = await apiRequest("/groups/developers");
            
            data.Developers.forEach(dev => {
                const option = buildElement("option", "", `${dev.username} (${dev.role})`);
                option.value = dev.id;

                developerSelect.appendChild(option);
            })
        }

        catch(error){
            showMessage(assignTaskSection, error.message, true);
        }

        form.addEventListener("submit", async function(event){

            event.preventDefault();

            const taskId = taskInput.value;
            const devId = developerSelect.value;

            try{

                const data = await apiRequest(`/tasks/${taskId}/assign`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({dev_id: Number(devId)})
                });

                showMessage(assignTaskSection, data.message)
            }

            catch(error){
                showMessage(assignTaskSection, error.message, true);
            }
        })
}

// Load the account details and select the appropriate task interface.
async function initializeTasksPage()
{
    try
    {
        currentAccount = await apiRequest("/account");

        if(currentAccount.account_status !== "active")
        {
            showMessage(taskListSelection, "Your account is not active", true);
            return;
        }

        sessionStorage.setItem("username", currentAccount.username);

        renderCreateTaskForm();

        await renderAssignTaskForm();
        await loadTasks();
    }

    catch(error)
    {
        showMessage(taskListSelection, error.message, true);
    }
}

initializeTasksPage();