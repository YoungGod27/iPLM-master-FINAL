function checkinginput(){
		var inputv = document.getElementById("input").value;
		
			if (inputv === "")
			{
				alert("Please enter your GWA");
				return false;
				
			}
			else if (inputv <= 2.5 && inputv >=1)
			{
				window.location="shifter3.html";
				return false;
			}
			else if (inputv > 2.5 && inputv <= 5)
			{
				window.location="shifter3.2.html";
				return false;
			}
		}
