var img = document.getElementById('liveImg');
var fpsText = document.getElementById('fps');
var frameNumText = document.getElementById('frameNum');

var target_fps = 24;

var request_start_time = performance.now();
var start_time = performance.now();
var time = 0;
var request_time = 0;
var time_smoothing = 0.9; // larger=more smoothing
var request_time_smoothing = 0.2; // larger=more smoothing
var target_time = 1000 / target_fps;

var wsProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://';

var path = location.pathname.replace('index.html', '/');
var ws = new WebSocket(wsProtocol + location.host + path + 'websocket');
ws.binaryType = 'arraybuffer';

/// Render / Layout

var renderState = {
  frameNum: 0,
  fps: 0
};

function setupLayout() {
  Object.assign(document.body.style, {
    padding: 0, margin: 0,
    backgroundColor: '#ccc'
  });

  Object.assign(img.style, {
    position: 'fixed',
    top: 0, left: 0, width: '100%', height: '100%',
    objectFit: 'cover'
  });
}

function updateRender() {
  const { frameNum, fps } = renderState;
  fpsText.textContent = fps;
  frameNumText.textContent = frameNum;
}

/// Image Handling

function requestImage() {
  request_start_time = performance.now();
  ws.send('more');
}

function handleImageMessage(arrayBuffer) {
  if (img.src) {
    URL.revokeObjectURL(img.src);
  }

  var blob  = new Blob([new Uint8Array(arrayBuffer)], {type: 'image/jpeg'});
  img.src = window.URL.createObjectURL(blob);

  // smooth with moving average
  var end_time = performance.now();
  var current_time = end_time - start_time;
  time = (time * time_smoothing) + (current_time * (1.0 - time_smoothing));
  start_time = end_time;
  renderState.fps = Math.round(1000 / time);

  // smooth with moving average
  var current_request_time = performance.now() - request_start_time;
  request_time = (request_time * request_time_smoothing) + (current_request_time * (1.0 - request_time_smoothing));
  var timeout = Math.max(0, target_time - request_time);

  setTimeout(requestImage, timeout);
}

/// Metadata

function handleMetadataMessage(data) {
  renderState.frameNum = data.frameNum;

  updateRender();
}

/// Websocket Events

ws.onopen = function() {
  console.log('connection was established');
  setupLayout();
  start_time = performance.now();
  requestImage();
};

ws.onmessage = function(evt) {
  if (typeof evt.data === 'string') {
    try {
      handleMetadataMessage(JSON.parse(evt.data));
    } catch (err) {
      console.log('JSON DECODE ERROR!', err);
    }
  } else {
    handleImageMessage(evt.data);
  }
};
