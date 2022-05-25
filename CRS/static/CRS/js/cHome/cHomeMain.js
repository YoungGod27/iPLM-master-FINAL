function _id(name) {
    return document.getElementById(name);
}

function _class(name) {
    return document.getElementsByClassName(name);
}
_class("toggle-password")[0].addEventListener("click", function () {
    _class("toggle-password")[0].classList.toggle("active");
    if (_id("password-field").getAttribute("type") == "password") {
        _id("password-field").setAttribute("type", "text");
    } else {
        _id("password-field").setAttribute("type", "password");
    }
});

_id("password-field").addEventListener("focus", function () {
    _class("password-policies")[0].classList.add("active");
});
_id("password-field").addEventListener("blur", function () {
    _class("password-policies")[0].classList.remove("active");
});

_id("password-field").addEventListener("keyup", function () {
    let password = _id("password-field").value;

    if (/[A-Z]/.test(password)) {
        _class("policy-uppercase")[0].classList.add("active");
    } else {
        _class("policy-uppercase")[0].classList.remove("active");
    }

    if (/[0-9]/.test(password)) {
        _class("policy-number")[0].classList.add("active");
    } else {
        _class("policy-number")[0].classList.remove("active");
    }

    if (/[^A-Za-z0-9]/.test(password)) {
        _class("policy-special")[0].classList.add("active");
    } else {
        _class("policy-special")[0].classList.remove("active");
    }

    if (password.length > 7) {
        _class("policy-length")[0].classList.add("active");
    } else {
        _class("policy-length")[0].classList.remove("active");
    }
});







function togglemenu() {
var y = document.getElementById("sidebar-wrapper");
if (y.style.display === "none") {
    y.style.display = "block";
} else {
    y.style.display = "none";
}

var x = document.getElementById("qlinks");
if (x.style.display === "none") {
    x.style.display = "block";
} else {
    x.style.display = "none";
}

}
        
// backtotop
function scrollFunction() {
    if (
      document.body.scrollTop > 20 ||
      document.documentElement.scrollTop > 20
    ) {
      mybutton.style.display = "block";
    } else {
      mybutton.style.display = "none";
    }
  }

  function backToTop() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
  }

  
function today() {
    // initializing an array 
    const months = [
        "January", "February", 
        "March", "April", "May", 
        "June", "July", "August",
        "September", "October", 
        "November", "December"
    ];

    const days = [
        "Monday", "Tuesday", 
        "Wednesday", "Thursday", "Friday", 
        "Saturday", "Sunday"
    ];

    const d = new Date();
    document.getElementById(
        "datetoday").innerHTML =        
        months[d.getMonth()] + " " + d.getDate();
    
        document.getElementById(
            "daytoday").innerHTML =        
            days[d.getDay()-1];

}