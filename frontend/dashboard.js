const API_BASE_URL = "http://127.0.0.1:12345";

// Dashboard HTML elements
const dashboardMessage = document.getElementById("dashboard-message");
const projectSection = document.getElementById("project-section");

// Current user's account information
let currentAccount = null;

// Task storage
let groupTasks = [];

// Display dashboard message
function showMessage(message, isError = false)
{
    dashboardMessage.textContent = message;

    dashboardMessage.style.color = isError ? "crimson" : "inherit";
}

// Create HTML elements
function buildElement(tagName, cssClass, textContent = "")
{
    const element = document.createElement(tagName);

    if(cssClass)
    {
        element.className = cssClass;
    }

    element.textContent = textContent;

    return element;
}

// Make authenticated API request
async function apiRequest(endpoint)
{
    const token = sessionStorage.getItem("access_token");

    if(!token)
    {
        window.location.href = "index.html";

        throw new Error("Your session has expired. Please log in again");
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    let data = {};

    try
    {
        data = await response.json();
    }

    catch
    {
        data = {};
    }

    if(!response.ok)
    {
        let detail = data.detail;

        if(Array.isArray(detail))
        {
            detail = detail.map(item => item.msg || String(item)).join(", ");
        }

        throw new Error(detail || data.message || `Request failed (${response.status}).`);
    }

    return data;
}

// Load group's assigned project
async function loadProject()
{
    try
    {
        const projectData = await apiRequest("/projects/my-project");
        const project = projectData.message;

        document.getElementById("project-name").textContent = project.project_name;
        document.getElementById("project-description").textContent = project.project_description;
        document.getElementById("project-status").textContent = project.project_status;
        document.getElementById("project-id").textContent = project.project_id;

        projectSection.classList.remove("hidden");

        await loadTasks();
    }

    catch(error)
    {
        if(error.message.startsWith("No project is assigned to"))
        {
            showMessage("Your group has not been assigned a project yet");
            return;
        }
        showMessage(error.message, true);
    }
}

// Load group's tasks
async function loadTasks()
{
    try
    {
        const taskData = await apiRequest(`/groups/${currentAccount.group_id}/tasks`);

        groupTasks = taskData.Tasks
        calculateTaskStatistics();
        renderTasks();

        showMessage("Dashboard Loaded Successfully");
    }

    catch(error)
    {
        showMessage(error.message, true);
    }
}

// Calculate task statistics
function calculateTaskStatistics()
{
    const totalTasks = groupTasks.length;

    const inProgress = groupTasks.filter(task => task.status === "in_progress").length;

    const completed = groupTasks.filter(task => task.status === "completed").length;

    const pending = groupTasks.filter(task => ["created", "on_hold", "assigned"].includes(task.status)).length;

    const progress = totalTasks === 0 ? 0 : Math.round((completed / totalTasks) * 100);

    document.getElementById("total-tasks").textContent = totalTasks;
    document.getElementById("in-progress-tasks").textContent = inProgress;
    document.getElementById("completed-tasks").textContent = completed;
    document.getElementById("pending-tasks").textContent = pending;

    document.getElementById("project-progress").value = progress;
    document.getElementById("progress-percentage").textContent = `${progress}% completed`;
}

// Render group's tasks
function renderTasks()
{
    const taskList = document.getElementById("task-list");

    taskList.innerHTML = "";

    if(groupTasks.length === 0)
    {
        taskList.textContent = "No tasks have been created for this project yet";
        return;
    }

    groupTasks.forEach(task => 
    {
        const taskCard = buildElement("article", "dashboard-card");

        const title = buildElement("h3", "", task.title);
        const description = buildElement("p", "", task.description);
        const status = buildElement("p", "", `Status: ${task.status}`);
        const priority = buildElement("p", "", `Priority: ${task.priority}`);
        const assignedTo = buildElement("p", "", `Assigned To: ${task.assigned_to || "Unassigned"}`);

        taskCard.append(title, description, status, priority, assignedTo);
        taskList.appendChild(taskCard);
    });
}

// Load current user's account
async function loadAccount()
{
    try
    {
        currentAccount = await apiRequest("/account");

        if(!["manager", "tech lead"].includes(currentAccount.role))
        {
            showMessage("You are not authorized to access this dashboard", true);
            return;
        }

        if(!currentAccount.group_id)
        {
            showMessage("Your Account is not assigned to any group.", true);
            return;
        }

        await loadProject();
    }

    catch(error)
    {
        showMessage(error.message, true);
    }
}

loadAccount();