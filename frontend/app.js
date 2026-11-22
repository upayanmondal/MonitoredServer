const API_BASE_URL = "http://127.0.0.1:12345";

const loginSection = document.getElementById("login-section");
const signupSection = document.getElementById("signup-section");

const dashboardSection = document.getElementById("dashboard-section");
const welcomeMessage = document.getElementById("welcome-message");
const authContainer = document.getElementById("auth-container");

const logoutButton = document.getElementById("logout-button");

// Manager & Tech Lead dashboard section And Button
const managerTechLeadDashboardCard = document.getElementById("manager-tech-lead-dashboard-card");
const managerTechLeadDashboardButton = document.getElementById("manager-tech-lead-dashboard-button");

// Admin panel section And Button
const adminDashboardCard = document.getElementById("admin-dashboard-card");
const adminDashboardButton = document.getElementById("admin-dashboard-button");

const profileButton = document.getElementById("profile-button");
const taskButton = document.getElementById("tasks-button");
const profileSection = document.getElementById("profile-section");
const backToDashboard = document.getElementById("back-to-dashboard");

// View Profile
const profileUsername = document.getElementById("profile-username");
const profileRole = document.getElementById("profile-role");
const profileExperience = document.getElementById("profile-experience");
const profileStatus = document.getElementById("profile-status");

// Edit Profile Form
const editProfileForm = document.getElementById("edit-profile-form");
const editUsername = document.getElementById("edit-username");
const editPassword = document.getElementById("edit-password");
const editExperience = document.getElementById("edit-experience");
const editProfileMessage = document.getElementById("edit-profile-message");


// Show Login or SignUP
const showSignup = document.getElementById("show-signup");
const showLogin = document.getElementById("show-login");

showSignup.addEventListener("click", function(event) {
    event.preventDefault();

    loginSection.classList.add("hidden");
    signupSection.classList.remove("hidden");
});

showLogin.addEventListener("click", function(event){
    event.preventDefault();

    signupSection.classList.add("hidden");
    loginSection.classList.remove("hidden");
});

function showDashboard(username)
{
    authContainer.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
    welcomeMessage.textContent = `Welcome, ${username}`; 
}

// Role based Dashboard
function updateRoleDashboard(role)
{
    managerTechLeadDashboardCard.classList.add("hidden");
    adminDashboardCard.classList.add("hidden");

    if(role == "manager" || role == "tech lead")
    {
        managerTechLeadDashboardCard.classList.remove("hidden");
    }

    else if(role == "admin")
    {
        adminDashboardCard.classList.remove("hidden");
    }
}

const loginForm = document.getElementById("login-form");
const loginUsername = document.getElementById("login-username");
const loginPassword = document.getElementById("login-password");
const loginMessage = document.getElementById("login-message");

loginForm.addEventListener("submit", async function(event){

    event.preventDefault();

    loginMessage.textContent = "Logging in......";

    try{
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(
                {
                    username: loginUsername.value,
                    password: loginPassword.value
                }
            )
        });

        const data = await response.json();

        if(!response.ok)
        {
            throw new Error(data.detail || "Login Failed");
        }

        loginMessage.textContent = data.message;

        sessionStorage.setItem("access_token", data.access_token);
        sessionStorage.setItem("username", data.username);

        const accountResponse = await fetch(`${API_BASE_URL}/account`, {
            headers: {
                "Authorization": `Bearer ${data.access_token}`
            }
        });

        if(!accountResponse.ok)
        {
            throw new Error("Unable to retrieve account information.");
        }

        const account = await accountResponse.json();

        updateRoleDashboard(account.role);

        loginSection.classList.add("hidden");
        signupSection.classList.add("hidden");
        dashboardSection.classList.remove("hidden");
        authContainer.classList.add("hidden");

        welcomeMessage.textContent = `Welcome, ${data.username}!`;
    }

    catch(error)
    {
        loginMessage.textContent = error.message;
    }
});

const signupForm = document.getElementById("signup-form");
const signupUsername = document.getElementById("signup-username");
const signupPassword = document.getElementById("signup-password");
const signupExperience = document.getElementById("signup-experience");
const signupMessage = document.getElementById("signup-message");

signupForm.addEventListener("submit", async function(event){
    event.preventDefault();

    signupMessage.textContent = "creating account..........";

    try{
        const response = await fetch(`${API_BASE_URL}/signup`,{
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username: signupUsername.value,
                    password: signupPassword.value,
                    experience: parseInt(signupExperience.value, 10)
                })
            });
        
        const data = await response.json();

        if(!response.ok)
        {
            throw new Error(data.detail || "signup failed");
        }

        signupMessage.textContent = data.message;
        signupForm.reset();
    }
    catch(error)
    {
        signupMessage.textContent = error.message;
    }
});

async function restoreSession()
{
    const savedToken = sessionStorage.getItem("access_token");
    
    if(!savedToken)
    {
        return;
    }

    try{
        const response = await fetch(`${API_BASE_URL}/account`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${savedToken}`
            }
        });

        if(response.status === 401)
        {
            sessionStorage.removeItem("access_token");
            sessionStorage.removeItem("username");
            return;
        }

        if(!response.ok)
        {
            throw new Error("Unable to verify your session. Please try again.");
        }

        const account = await response.json();

        sessionStorage.setItem("username", account.username);

        showDashboard(account.username);
        updateRoleDashboard(account.role);
    }
    catch(error)
    {
        loginMessage.textContent = error.message;
    }
}

restoreSession();

logoutButton.addEventListener("click", async function(){
    const savedToken = sessionStorage.getItem("access_token");

    try
    {
        if(savedToken)
        {
            const response = await fetch(`${API_BASE_URL}/logout`,{
                method: "POST",
                headers : {
                    "Authorization": `Bearer ${savedToken}`
                }
            });

            if(!response.ok)
            {
                throw new Error("Server could not revoked your token");
            }
        }
    }
    catch(error)
    {
        console.error("Logout request failed: ", error);
    }
    finally
    {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("username");

        managerTechLeadDashboardCard.classList.add("hidden");
        adminDashboardCard.classList.add("hidden");

        dashboardSection.classList.add("hidden");
        authContainer.classList.remove("hidden");

        loginSection.classList.remove("hidden");
        signupSection.classList.add("hidden");

        loginForm.reset();
        loginMessage.textContent = "";
        signupMessage.textContent = "";
    }
});

profileButton.addEventListener("click", async function(){
    
    const savedToken = sessionStorage.getItem("access_token");

    try
    {
        const response = await fetch(`${API_BASE_URL}/account`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${savedToken}`
            }
        });

        const data = await response.json();

        if(!response.ok)
        {
            throw new Error(data.detail || "Failed to fetch profile");
        }

        profileUsername.textContent = data.username;
        profileRole.textContent = data.role;
        profileExperience.textContent = data.experience;
        profileStatus.textContent = data.account_status;

        dashboardSection.classList.add("hidden");
        profileSection.classList.remove("hidden");
    }
    catch(error)
    {
        console.error("Error fetching profile: ", error);
    }

});

backToDashboard.addEventListener("click", function()
{
    profileSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
});

taskButton.addEventListener("click", function(){
    console.log("The task button is clicked");
    window.location.href = "./tasks.html";
});

managerTechLeadDashboardButton.addEventListener("click", function()
{
    window.location.href = "./dashboard.html";
});

adminDashboardButton.addEventListener("click", function()
{
    window.location.href = "./admin.html";
});

editProfileForm.addEventListener("submit", async function(event){
    event.preventDefault();

    const savedToken = sessionStorage.getItem("access_token");

    if(!savedToken)
    {
        editProfileMessage.textContent = "Your session has expired. Please log in again.";
        return;
    }
    
    const updatedProfile = {};

    if(editUsername.value.trim() != "")
    {
        updatedProfile.username = editUsername.value.trim();
    }

    if(editPassword.value.trim() != "")
    {
        updatedProfile.password = editPassword.value;
    }

    if(editExperience.value.trim() != "")
    {
        updatedProfile.experience = editExperience.value.trim();
    }

    // If nothing to update
    if(Object.keys(updatedProfile).length === 0)
    {
        editProfileMessage.textContent = "No changes to save.";
        return;
    }

    try{
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: "PUT",
            headers:{
                "Content-Type": "application/json",
                "Authorization": `Bearer ${savedToken}`
            },
            body: JSON.stringify(updatedProfile)
        });

        const data = await response.json();

        if(!response.ok)
        {
            throw new Error(data.detail || "Failed to update profile");
        }

        editProfileMessage.textContent = data.message || "Profile updated successfully.";

        if(updatedProfile.username !== undefined)
        {
            profileUsername.textContent = updatedProfile.username;

            sessionStorage.setItem("username", updatedProfile.username);
            sessionStorage.setItem("access_token", data.access_token)
        }

        if(updatedProfile.experience !== undefined)
        {
            profileExperience.textContent = updatedProfile.experience;
        }

        editProfileForm.reset();
    }

    catch(error)
    {
        editProfileMessage.textContent = error.message;
    }

});