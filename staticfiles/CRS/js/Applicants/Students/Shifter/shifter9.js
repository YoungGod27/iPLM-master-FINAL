
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
			if (document.getElementById('LetterofIntentFile').value == ""){
			errormessage += "Upload your Letter of Intent\n";
			}
			if (document.getElementById('GradeScreenshotFile').value == ""){
			errormessage += "Upload your Screenshot of Grades\n";
			}
			if (errormessage != ""){
			alert(errormessage)
			return false;
			}
		}