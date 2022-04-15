//---------------------
// Scrolling
//---------------------




//---------------------
// Hide/Show Divisions
//---------------------

// Function to hide other divisions when one is clicked
// use onclick = "showdiv('yourdivid')"  to implement this
// Also use display: none for the CSS of the block that needs to be hidden at start

var _hidediv = null;

function showdiv(id) {
	if(_hidediv) {
		_hidediv();
	}
	var div = document.getElementById(id);
	div.style.display = 'block';
	_hidediv = function () {
		div.style.display = 'none'; 
	};
}


//-------------------------
// ADD CLASS TO AN ELEMENT
//-------------------------

function addClass(element, idPrefix, className) {
	var matching_elements = document.querySelectorAll('[id*='+idPrefix+']');
	for(var i = 0; i < matching_elements.length; i++) {
		matching_elements[i].classList.remove(className);
	}
	element.classList.add(className);
}


//-------------------------
// ADD STYLESHEET (add theme css file)
//-------------------------

// TODO: currently disabled, not implemented

// function toggleStyleSheet() {
// 	// get all link tags in the document
// 	var links = document.getElementsByTagName("link");
// 	// loop through each link tag
// 	for(var i = 0; i < links.length; i++) {
// 		// Find link tag containing the theme css file. There should be only one. But if there are more than one, remove them all anyways :D
// 		if(links[i].href.indexOf('theme') > -1) {
// 			// if theme css file is found, remove it
// 			links[i].parentNode.removeChild(links[i]);
// 		}
		
// 	}
// }