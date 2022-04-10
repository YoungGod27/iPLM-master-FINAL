function checkforblank()
		{
			var errormessage = "";
			if (document.getElementById('StudNum').value == ""){
			errormessage += "Enter your Student Number\n";
			}
			if (document.getElementById('LastName').value == ""){
			errormessage += "Enter your Last Name\n";
			}
			if (document.getElementById('FirstName').value == ""){
			errormessage += "Enter your First Name\n";
			}
			if (document.getElementById('EmailAddress').value == ""){
			errormessage += "Enter your Email Address\n";
			}
			if (document.getElementById('Phone').value == ""){
			errormessage += "Enter your Phone Number\n";
			}
			if (document.getElementById('HonDis').value == ""){
			errormessage += "Upload your Honorable Dismissal\n";
			}
			if (document.getElementById('GoodMoral').value == ""){
			errormessage += "Upload your Good Moral\n";
			}
			if (document.getElementById('NOU').value == ""){
			errormessage += "Upload your Note of Undertaking\n";
			}
			if (document.getElementById('Grades').value == ""){
			errormessage += "Upload your Screenshot of Grades\n";
			}
			if (errormessage != ""){
			alert(errormessage)
			return false;
			}
		}