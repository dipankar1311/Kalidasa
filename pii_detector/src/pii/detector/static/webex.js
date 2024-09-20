`
var script = document.createElement('script');
script.src = "https://10.53.60.89/static/webex.js";
document.getElementsByTagName('head')[0].appendChild(script);
`

var recognition = null;


function prepare() {
    if ('webkitSpeechRecognition' in window) {
        console.log("webkitSpeechRecognition OK");
        recognition = new webkitSpeechRecognition();
        
        // Set parameters
        recognition.continuous = true;  // Enable continuous recognition
        recognition.interimResults = true;  // Enable interim results
      
        console.log("Recognition before start");
        recognition.onstart = function() {
          console.log('Speech recognition started');
        }


        recognition.onspeechend = function() {
            console.log('Speech recognition onspeechend');
            prepare();
        }

        console.log("Recognition after start");
      
        recognition.onresult = function(event) {
          for (var i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    console.log(event.results[i][0].transcript);
                    make_request(event.results[i][0].transcript);
                }
            }
        }

        // Start listening
        recognition.start();
    }
    else {
        console.error("webkitSpeechRecognition not found");
    }
}

prepare();

function make_request(text) {
    // Send this text as a JSON to the server
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "https://10.53.60.89/process_text/", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({text: text}), null, 4);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            console.log(xhr.responseText);

            var response = JSON.parse(xhr.responseText);

            var discussingPIIEntitity = "";
            if (response.discussing_pii_entity) {
                discussingPIIEntitity = `* What: '${response.discussing_pii_entity}' <br/>`;
            }

            var intentClassification = "";
            if (response.intent_classification) {
                intentClassification = `* Intent: '${response.intent_classification}' <br/>`;
            }

            var pii_found = "";
            if (response.pii_info_found && response.pii_info_found.length > 0) {
                pii_found = `* PII Found: '${response.pii_info_found}' <br/>`;
            }

            var spacer = "";
            if (discussingPIIEntitity.length > 0 || intentClassification.length > 0 || response.pii_info_found.length > 0) {
                spacer = "<br/>";
            }

            console.log(JSON.stringify(response, null, 4));
            if (response.is_discussing_pii == true) {
                // Find class pii_desc_container and set text in it
                document.getElementsByClassName("pii_desc_container")[0].innerHTML = `
                ${spacer}
                ${discussingPIIEntitity}
                ${pii_found}
                ${intentClassification}
                `;
                // Show the hackathon div
                document.getElementById("hackathon").style.display = "block";
            }
            else {
                document.getElementsByClassName("pii_desc_container")[0].textContent = "";
            }
        }
    }
}
make_request("test");

var html = `
<div id="hackathon" style="width: 250px;position: fixed;background: black;box-shadow: 0px 0px 4px 1px #D84315;border-radius: 8px; top: 50%; right: 50%; transform: translate(50%,-50%);color: white;padding: 5px;z-index: 999; display: none;">
    <div style="
    text-align: center;
    border-bottom: 1px solid #333333;
    padding-bottom: 2px;
">
        Caution
    </div>
    <span id="id_dismiss" title="Dismiss" style="
        position: absolute;
        right: 15px;
        top: 3px; cursor: pointer;
    ">x</span>

    

    <div style="
    height: calc(100% - 55px);
    padding: 5px;
    font-size: 80%;
">
    You could be discussing Personal Identifiable Information (PII). <br/> Remember, your Personal Identifiable Information (PII) is sensitive. Avoid sharing it to protect your privacy and prevent potential misuse. Stay safe, stay secure.
    <div class="pii_desc_container"></div>
    </div>

    <div style="
    border-top: 1px solid #333333;
    padding-bottom: 2px;
    font-size: 70%;
    padding: 4px;
    color: lightblue;
">
        Keep Cisco Safe <a href="https://www.cisco.com/c/en/us/solutions/collateral/enterprise/design-zone-security/safe-overview-guide.html">🔗</a>
    </div>
</div>
`;
// Append html to body tag
document.body.innerHTML += html;

// Add click event handler to id "id_dismiss"
document.getElementById("id_dismiss").addEventListener("click", function() {
    document.getElementById("hackathon").style.display = "none";
});

// load a javascript file
var script = document.createElement('script');
script.src = ""
document.getElementsByTagName('head')[0].appendChild(script);
