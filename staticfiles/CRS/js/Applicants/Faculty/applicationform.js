function checkforblank() {

    var errormessage = "";

    if (document.getElementById('LastName').value == "") {
        errormessage += "Enter Your Last Name \n";
        }
    if (document.getElementById('FirstName').value == "") {
        errormessage += "Enter Your First Name \n";
        }
    if (document.getElementById('EmailAddress').value == "") {
        errormessage += "Enter Your Email Address \n";
        }
    if (document.getElementById('Phone').value == "") {
        errormessage += "Enter Your Phone Number \n";
        }
    if (document.getElementById('CVFile').value == "") {
        errormessage += "Upload your CV File \n";
        }
    if (document.getElementById('CertificateFile').value == "") {
        errormessage += "Upload your Certicates File \n";
        }
    if (document.getElementById('CredentialsFile').value == "") {
        errormessage += "Upload your Credentials \n";
        }
    if (document.getElementById('TORFile').value == "") {
        errormessage += "Upload your TOR \n";
        }
    if (errormessage != "") {
        alert(errormessage);
        return false;
        }
    }