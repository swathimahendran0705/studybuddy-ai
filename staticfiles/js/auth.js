document.getElementById("regForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    let form = new FormData(e.target);

    let res = await fetch("/auth/register/", {
        method: "POST",
        body: form
    });
    let data = await res.json();

    alert(data.message || data.error);
});

document.getElementById("loginForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    let form = new FormData(e.target);

    let res = await fetch("/auth/login/", {
        method: "POST",
        body: form
    });
    let data = await res.json();

    if (data.message) {
        window.location.href = "/home/";
    } else {
        alert(data.error);
    }
});
