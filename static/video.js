
socket = io();
// Connect to the WebSocket server
socket.connect('https://divineux23-code50-96517814-445597p7x7f5rx6-5000.preview.app.github.dev/');
// When the SocketIO connection is established
socket.on('connect', function() {
console.log('Connected to server');
});

  // Send user input to the server when the form is submitted
  const form = document.getElementById('chat-form');
  console.log(form);
  const input = document.getElementById('user_input');
  const chat = document.getElementById('conversation-history');

  form.addEventListener('submit', function(event) {
  event.preventDefault();
  console.log('Form submitted');
  console.log(input.value);
  const message = document.createElement('div');
  message.innerHTML = `<span class="user-label">YOU:</span> ${input.value}`;

  message.classList.add('user-message');
  chat.appendChild(message);
  socket.emit('user_input', input.value);
  input.value = '';
});


  // Listen for incoming bot responses
  socket.on('bot_response', function(data) {

  // Update the chat UI with the bot response
  console.log(data);
  const chat = document.getElementById('conversation-history');
  const message = document.createElement('div');

  const ai = document.createElement('span');
  ai.innerText = '😎: ';
  ai.style.color = 'blue';
  ai.style.fontWeight = 'bold';
  ai.style.fontSize = '20px';

  message.appendChild(ai);

  const response = document.createElement('span');
  response.innerText = data;
  response.style.color = 'black';

  message.appendChild(response);

  message.classList.add('bot-message');

  chat.appendChild(message);

});


//Deleting the video

window.addEventListener("beforeunload", function(event) {
var xhr = new XMLHttpRequest();
xhr.open("POST", "/delete_video", true);
xhr.send();
});


var timeout;

function deleteVideoFile() {
var xhr = new XMLHttpRequest();
xhr.open('POST', '/delete_video', true);
xhr.send();
}

function startTimeout() {
timeout = setTimeout(deleteVideoFile, 1800000);
}

function clearTimeoutIfInteracted() {
clearTimeout(timeout);
document.removeEventListener('mousemove', clearTimeoutIfInteracted);
}

function clearTimeIfInteracted(){
clearTimeout(timeout);
document.removeEventListener('click', clearTimeoutIfInteracted);
}
function clearAndDelete() {
clearTimeout(timeout);
deleteVideoFile();
}

startTimeout();

document.addEventListener('click', clearTimeoutIfInteracted);

document.addEventListener('mousemove', clearTimeoutIfInteracted);

window.addEventListener('beforeunload', clearAndDelete);
