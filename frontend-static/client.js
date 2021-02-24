var img = document.getElementById('liveImg');
var screenEl = document.getElementById('screen');
var fpsText = document.getElementById('fps');
var frameNumText = document.getElementById('frameNum');
var actionHistoryEl = document.getElementById('action-history');
var aiLogEl = document.getElementById('ai-log');
var stateActionsEl = document.getElementById('state-actions');
var objectAnnCanvas = document.getElementById('object-annotations');
var stats = document.getElementById('stats');
var titleEl = document.getElementById('rodeo');
var resetCoverEl = document.getElementById('reset-cover')
var resetEmojisEl = document.getElementById('reset-emojis')

var SHOW_RESET_SCREEN = true;
var SHOW_NEW_MONEY_ANIMATION = false;

var target_fps = 13;

var request_start_time = performance.now();
var start_time = performance.now();
var time = 0;
var request_time = 0;
var time_smoothing = 1.2; // larger=more smoothing
var request_time_smoothing = 0.2; // larger=more smoothing
var target_time = 1000 / target_fps;

var sounds = {
  'tap_location': {src:'Rodeo-single-click.wav'},
  'double_tap_location':{src:'Rodeo-double-click.wav'} ,
  'swipe':{src:'Rodeo-swipe.wav'} ,
  'reset': {src:'Rodeo-restart.wav', delay: 3500}
};

var wsProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://';

var path = location.pathname.replace('index.html', '/');
var ws = new WebSocket(wsProtocol + location.host + path + 'websocket');
ws.binaryType = 'arraybuffer';

var playing = true

/// Render / Layout

const colors = JSON.parse(`{
  "aliceblue": "#f0f8ff", "antiquewhite": "#faebd7", "aqua": "#00ffff", "aquamarine": "#7fffd4", "azure": "#f0ffff", "beige": "#f5f5dc", "bisque": "#ffe4c4", "black": "#000000", "blanchedalmond": "#ffebcd", "blue": "#0000ff", "blueviolet": "#8a2be2", "brown": "#a52a2a", "burlywood": "#deb887", "cadetblue": "#5f9ea0", "chartreuse": "#7fff00", "chocolate": "#d2691e", "coral": "#ff7f50", "cornflowerblue": "#6495ed", "cornsilk": "#fff8dc", "crimson": "#dc143c", "cyan": "#00ffff", "darkblue": "#00008b", "darkcyan": "#008b8b", "darkgoldenrod": "#b8860b", "darkgray": "#a9a9a9", "darkgreen": "#006400", "darkgrey": "#a9a9a9", "darkkhaki": "#bdb76b", "darkmagenta": "#8b008b", "darkolivegreen": "#556b2f", "darkorange": "#ff8c00", "darkorchid": "#9932cc", "darkred": "#8b0000", "darksalmon": "#e9967a", "darkseagreen": "#8fbc8f", "darkslateblue": "#483d8b", "darkslategray": "#2f4f4f", "darkslategrey": "#2f4f4f", "darkturquoise": "#00ced1", "darkviolet": "#9400d3", "deeppink": "#ff1493", "deepskyblue": "#00bfff", "dimgray": "#696969", "dimgrey": "#696969", "dodgerblue": "#1e90ff", "firebrick": "#b22222", "floralwhite": "#fffaf0", "forestgreen": "#228b22", "fuchsia": "#ff00ff", "gainsboro": "#dcdcdc", "ghostwhite": "#f8f8ff", "goldenrod": "#daa520", "gold": "#ffd700", "gray": "#808080", "green": "#008000", "greenyellow": "#adff2f", "grey": "#808080", "honeydew": "#f0fff0", "hotpink": "#ff69b4", "indianred": "#cd5c5c", "indigo": "#4b0082", "ivory": "#fffff0", "khaki": "#f0e68c", "lavenderblush": "#fff0f5", "lavender": "#e6e6fa", "lawngreen": "#7cfc00", "lemonchiffon": "#fffacd", "lightblue": "#add8e6", "lightcoral": "#f08080", "lightcyan": "#e0ffff", "lightgoldenrodyellow": "#fafad2", "lightgray": "#d3d3d3", "lightgreen": "#90ee90", "lightgrey": "#d3d3d3", "lightpink": "#ffb6c1", "lightsalmon": "#ffa07a", "lightseagreen": "#20b2aa", "lightskyblue": "#87cefa", "lightslategray": "#778899", "lightslategrey": "#778899", "lightsteelblue": "#b0c4de", "lightyellow": "#ffffe0", "lime": "#00ff00", "limegreen": "#32cd32", "linen": "#faf0e6", "magenta": "#ff00ff", "maroon": "#800000", "mediumaquamarine": "#66cdaa", "mediumblue": "#0000cd", "mediumorchid": "#ba55d3", "mediumpurple": "#9370db", "mediumseagreen": "#3cb371", "mediumslateblue": "#7b68ee", "mediumspringgreen": "#00fa9a", "mediumturquoise": "#48d1cc", "mediumvioletred": "#c71585", "midnightblue": "#191970", "mintcream": "#f5fffa", "mistyrose": "#ffe4e1", "moccasin": "#ffe4b5", "navajowhite": "#ffdead", "navy": "#000080", "oldlace": "#fdf5e6", "olive": "#808000", "olivedrab": "#6b8e23", "orange": "#ffa500", "orangered": "#ff4500", "orchid": "#da70d6", "palegoldenrod": "#eee8aa", "palegreen": "#98fb98", "paleturquoise": "#afeeee", "palevioletred": "#db7093", "papayawhip": "#ffefd5", "peachpuff": "#ffdab9", "peru": "#cd853f", "pink": "#ffc0cb", "plum": "#dda0dd", "powderblue": "#b0e0e6", "purple": "#800080", "rebeccapurple": "#663399", "red": "#ff0000", "rosybrown": "#bc8f8f", "royalblue": "#4169e1", "saddlebrown": "#8b4513", "salmon": "#fa8072", "sandybrown": "#f4a460", "seagreen": "#2e8b57", "seashell": "#fff5ee", "sienna": "#a0522d", "silver": "#c0c0c0", "skyblue": "#87ceeb", "slateblue": "#6a5acd", "slategray": "#708090", "slategrey": "#708090", "snow": "#fffafa", "springgreen": "#00ff7f", "steelblue": "#4682b4", "tan": "#d2b48c", "teal": "#008080", "thistle": "#d8bfd8", "tomato": "#ff6347", "turquoise": "#40e0d0", "violet": "#ee82ee", "wheat": "#f5deb3", "white": "#ffffff", "whitesmoke": "#f5f5f5", "yellow": "#ffff00", "yellowgreen": "#9acd32"
}`)

var renderState = {
  frameNum: 0,
  fps: 0,
  imageState: null,
  recentTouch: null,
  stateActions: [],
  aiStepNum: 0,
  aiReward: 0,
  aiPolicyChoice: null,
  aiRecentActionStepNums: {},
  systemInfo: {},
  actionHistory: [],
  aiLogs: [],
  showingResetScreen: false,
  playingNewMoneyAnimation: false,
};

function readTextFile(file, callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.overrideMimeType("application/json");
    rawFile.open("GET", file, true);
    rawFile.onreadystatechange = function() {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(rawFile.responseText);
        }
    }
    rawFile.send(null);
}
var emojiPositions = actionEmoji = {}
//usage:
readTextFile("./emojimap.json", function(text){
    emojiPositions = JSON.parse(text);
    actionEmoji = {
      tap_location: emoji("point"),
      double_tap_location: emoji("point")+emoji("point"),
      swipe_right:  emoji("point")+emoji("right_arrow"),
      swipe_left: emoji("left_arrow")+ emoji("point"),
      reset: emoji("siren"),
    }

    titleEl.innerHTML = `${emoji("goat")} ⋆ ${emoji("rabbit")}  ${emoji("ribbon")}  /𝓇${emoji("blueheart")}ʊˈ𝒹𝑒ɪ❤ʊ/ 𝐿𝑒𝓉𝓈 𝒫𝓁𝒶𝓎 𝐻${emoji("hearteyes")}𝐿𝐿𝒴𝒲${emoji("cookie")}❤𝒟 𝓋 𝟣.♡  ${emoji("ribbon")}  ${emoji("rabbit")} ⋆ ${emoji("goat")}`
    titleEl.style.zIndex = "111"
});

function replaceWithEmojis(str){
    var re = new RegExp(Object.keys(emojiPositions).join("|"),"gi");
    return str.replace(re, function(matched){
        return emoji(matched);
    });
}

function stripStrings(substrings,str){
    var re = new RegExp(substrings.join("|"),"gi");
    return str.replace(re,"");
}

var emojiSize = 28;


function emoji(emojiName) {
  var mapData = emojiPositions[emojiName] || [[0,0]];
  //make sure we have an array of arrays, in case multiple emojis should be shown
  var emojis = (typeof mapData[0] === "object" ? mapData : [mapData]);

  return emojis.map( emoj => `<span class='emoji' style="background-position: ${(emoj[0]*(emojiSize))} ${emoj[1]*emojiSize};"></span>`).join("");
}

function updateCurStateRender() {
  const { frameNum, fps, imageState, recentTouch, stateActions = [], systemInfo } = renderState;
  renderImageState(imageState, recentTouch);
}

/// Image State Rendering

const labelColorsMap = {
  'person': colors['blueviolet'],
  'clock': colors['springgreen'],
  'tvmonitor': colors['black'],
  'laptop': colors['black'],
  'traffic light': colors['chartreuse'],
  'chair': colors['saddlebrown'],
  'cell phone': colors['darkgrey'],
  'bicycle': colors['gold'],
  'car': colors['royalblue'],
  'skateboard': colors['orange'],
  'sports ball': colors['maroon'],
  'bottle': colors['beige'],
  'banana': colors['yellow'],
  'umbrella': colors['salmon'],
  'frisbee': colors['sienna'],
  'teddy bear': colors['brown']
}

function initSound(){
  for(i in sounds){
    sounds[i].clip = new Howl({
      src: sounds[i].src
    });
  }
  console.log("sounds loaded")
}

function playSound(sound){
  setTimeout(function(){
    sounds[sound].clip.stop();
    sounds[sound].clip.play();
  }, sounds[sound].delay || 0)
}

initSound();

function getImageObjectColor(label, confidence) {
  if (labelColorsMap[label])    return labelColorsMap[label]
  if (label.includes('Circle')) return colors['cornflowerblue']
  if (label.includes('Blob'))   return colors['purple']
  if (!confidence)              return colors['black']
  if (confidence > 0.75)        return colors['b']
  if (confidence > 0.5)         return colors['darkorchid']
  if (confidence > 0.25)        return colors['gold']
  else                          return colors['white']
}

function drawLine(ctx, p1x, p1y, p2x, p2y) {
  ctx.beginPath();
  ctx.moveTo(p1x, p1y);
  ctx.lineTo(p2x, p2y);
  ctx.stroke();
}

function getCanvasSize() {
  const { width: w, height: h } = objectAnnCanvas
  return [w, h]
}

function translatePointToScreen(image_shape, x, y) {
  const [w1, h1] = image_shape
  const [w2, h2] = getCanvasSize()

  // https://math.stackexchange.com/questions/1857632/translating-co-ordinate-from-one-rectangle-to-another-rectangle
  const xNew = (x / w1) * w2
  const yNew = (y / h1) * h2
  return [xNew, yNew]
}

function translateRectToScreen(image_shape, x, y, w, h) {
  const [xNew, yNew] = translatePointToScreen(image_shape, x, y)

  const [w1, h1] = image_shape
  const [w2, h2] = getCanvasSize()
  const wNew = (w2 / w1) * w
  const hNew = (h2 / h1) * h

  return [xNew, yNew, wNew, hNew]
}

// imageState is the JSON equivalent of the python AIState object :)
function renderImageState(imageState, recentTouch) {
  if (!imageState) {
    return;
  }

  // console.log(renderState.frameNum, imageState, recentTouch)

  const canvas = objectAnnCanvas;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const { image_objects = [], image_shape } = imageState;

  // draw each object on top of main image
  image_objects.forEach(item => {
    let { label, confidence, object_type: type, rect, circle, shape_data } = item

    const style = {
      color: getImageObjectColor(label, confidence),
      fontSize: 18,
      fontFamily: "Cursive",
      fontWeight: 'normal'
    }

    // Special handling of action_shape objects to remove color label if we know the color :)
    if (type == 'action_shape') {
      style.fontWeight = 'medium';
      if (shape_data) {
        colorKey = (shape_data.color_label || '').toLowerCase().replace(/ /g, '')
        style.color = colors[colorKey] || style.color
        label = shape_data.shape_label || label
      }
    }

    // Set style
    ctx.restore();
    ctx.strokeStyle = style.color;
    ctx.lineWidth = 3;
    ctx.font = `normal ${style.fontWeight} ${style.fontSize}px Helvetica Neue Roman`;
    // Draw Image Shape
    let textPoint = { x: 0, y: 0 }
    if (circle) {
      const [xRaw, yRaw, r] = circle
      const [x, y] = translatePointToScreen(image_shape, xRaw, yRaw)
      textPoint = { x: x + r + 10, y: y + 5 }
      ctx.arc(x, y, r, 0, 2 * Math.PI);
    } else {
      const [xRaw, yRaw, wRaw, hRaw] = rect
      const [x, y, w, h] = translateRectToScreen(image_shape, xRaw, yRaw, wRaw, hRaw)
      textPoint = { x: x + w + 10, y: y + 10 }
      ctx.strokeRect(x, y, w, h);
    }

    // Draw Text
    const text = confidence ? `${label} ${confidence.toFixed(2)}` : label;
    ctx.fillStyle = style.color;
    ctx.shadowOffsetX = 3;
    ctx.shadowOffsetY = 3;
    ctx.shadowBlur = 4;
    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
    ctx.fillText(text, textPoint.x, textPoint.y);
  })

  if (recentTouch && recentTouch.p) {
    const { p, type } = recentTouch
    const color = type === 'double_tap_location' ? '#328eed' : '#ed3732'

    // draw crosshairs
    // const [x, y] = p
    // const [h, w] = image_shape
    const [x, y] = translatePointToScreen(image_shape, p[0], p[1])
    const [w, h] = getCanvasSize()
    const r = 3
    ctx.lineWidth = 3
    ctx.strokeStyle = color
    drawLine(ctx, w, y, x + r, y)
    drawLine(ctx, x, 0, x, y - r)
    drawLine(ctx, 0, y, x - r, y)
    drawLine(ctx, x, h, x, y + r)
    ctx.fillStyle = color
    ctx.fillRect(x - r, y - r, r * 2, r * 2)

    if (recentTouch.prob) {
      ctx.fillText(`${Math.round(recentTouch.prob)}`, x + 8, y - 8)
    }
  }
}

function renderStateActions(stateActions) {
  const actionEls = (stateActions || [])
    .filter(a => a.length > 1 && !!a[1].object_type) // only render tap object actions :)
    .map((a, i) => {
      const v = a[1]
      const el = document.createElement('div')
      const text = `
        Action #${i + 1}:
        ${v.object_type || v.type}
        (${v.x}, ${v.y})
        ${v.img_obj ? ` - ${((v.img_obj.confidence || 0) * 100).toFixed(1)}%` : ''}
      `
      el.textContent = text
      return el
    })

  stateActionsEl.innerHTML = ``
  stateActionsEl.append(...actionEls)
}


function parseActionLog(actionString){
  //actionString = `Step 85 (1803) - Action (double_tap_location, {"x": 824, "y": 466, "type": "object", "object_type": "Circle #7", "img_obj": {"rect": [785, 427, 78, 78], "label": "Circle #7", "confidence": null, "object_type": "circle"}})`
  var split = actionString.split(" ");
  var actionNumber = split[1];
  var actionType = split[5].slice(1,-1).replace("(","")
  // if(actionType.indexOf("swipe")> -1)
  //     playSound("swipe");
  var actionJson = stripStrings(["{","}","\[","\]"],replaceWithEmojis(JSON.stringify(
        JSON.parse(actionString.slice(actionString.indexOf("{"),-1))
        ,{},'jsonemoji')))
  return `
  <div class='recent-action'>${replaceWithEmojis("Action "+actionNumber+" "+actionType)}</div>
  <div class='action-json'>${actionJson}</div>
  `
}

function stripParens(str){
  return str.replace(")","").replace("(","")
}

function renderAiLogs(aiLogs) {
  //take out action logs and put in action-history div
  
  const noActions = aiLogs.filter((log)=> {
    if(log.indexOf(" Action ")>-1){
      actionHistoryEl.innerHTML = `<pre>${parseActionLog(log)}</pre>`
      return false
    }
    return true
  })
  const logEls = []
  for (let i = (noActions || []).length - 1; i >= 0; i--) {
    logEls.push(transformAiLogs(noActions[i]))
  }
  if(noActions[noActions.length-1].indexOf("Chose") > -1){
    aiLogEl.innerHTML = ``
    aiLogEl.append(...logEls)
  }
}

function renderSystemInfo(systemInfo) {
  // console.log('system info', systemInfo)
  if (!systemInfo) {
    return
  }
}

function showResetScreen() {
  if (!SHOW_RESET_SCREEN || renderState.showingResetScreen) {
    return
  }

  renderState.showingResetScreen = true
  resetCoverEl.style.display = 'block'
  setTimeout(function() { resetCoverEl.style.opacity = 0.9 }, 5)
  setTimeout(function() { resetEmojisEl.style.display = 'block' }, 500)

  var resetDelay = 11000
  setTimeout(function() { resetCoverEl.style.opacity = 0 }, resetDelay - 500)
  setTimeout(function() {
    renderState.showingResetScreen = false
    resetCoverEl.style.display = 'none'
    resetEmojisEl.style.display = 'none'
  }, resetDelay)
}

function playNewMoneyAnimation() {
  if (!SHOW_NEW_MONEY_ANIMATION || renderState.playingNewMoneyAnimation) {
    return
  }

  renderState.playingNewMoneyAnimation = true

  var duration = 5000
  var items = 5
  var elements = []
  for (var i = 0; i < items; i++) {
    var el = document.createElement('div')
    el.innerHTML = emoji('moneybag')
    el.className = 'animating-money'
    el.style.left = (5 + Math.random() * 90) + '%'
    screenEl.appendChild(el)
    elements.push(el)
  }

  setTimeout(function() {
    elements.forEach(el => {
      el.style.opacity = 1
      el.style.top = (100 + Math.random() * 50) + '%';
    })
  }, 5)

  setTimeout(function() {
    elements.forEach(el => { el.style.opacity = 0 })
  }, duration - 300)
  setTimeout(function() {
    elements.forEach(el => { el.parentNode.removeChild(el) })
    renderState.playingNewMoneyAnimation = false
  }, duration)
}

/// Image Handling

function requestImage() {
  request_start_time = performance.now();
  ws.send('more');
}

function handleImageMessage(arrayBuffer) {
  if (playing) {
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
  }

  setTimeout(requestImage, timeout);
}

/// Data Updates

const parseMessageKey = (data, key) => typeof data[key] === 'string' ? JSON.parse(data[key]) : data[key]

function handleCurStateUpdate(data) {
  if (!playing) {
    return
  }

  var lastState = renderState.imageState

  renderState.frameNum = data.frameNum;
  renderState.imageState = parseMessageKey(data, 'imageState')
  renderState.systemInfo = parseMessageKey(data, 'systemInfo')

  const aiStatus = parseMessageKey(data, 'aiStatus') || {}
  renderState.stateActions = aiStatus.actions || []
  renderState.aiReward = aiStatus.reward || 0
  renderState.aiStepNum = aiStatus.step_num || 0
  renderState.aiPolicyChoice = aiStatus.policy_choice
  renderState.aiRecentActionStepNums = aiStatus.recent_action_step_nums

  if (lastState && lastState.money !== undefined && renderState.imageState && renderState.imageState.money > lastState.money) {
    playNewMoneyAnimation()
  }

  updateCurStateRender()
}

function pushToMaxLengthArray(arr, item, maxLength) {
  arr.push(item)
  if (arr.length > maxLength) {
    arr.shift() // remove first element of array to keep length at maxLength
  }
}

function handleAIActionUpdate(data) {
  if (!playing) {
    return
  }
  if(sounds && sounds[data.type]){
      playSound(data.type)
  }
  if (data.type === 'tap_location' || data.type === 'double_tap_location') {
    renderState.recentTouch = data
  } else {
    renderState.recentTouch = null
  }


  // if (data.type === 'reset') {
  //   showResetScreen()
  // }

  pushToMaxLengthArray(renderState.actionHistory, data, 50)
}
var aiLogChildren = 0;
var logsString = ""
var lineBuffer = [];
function handleAILogLineUpdate(line) {
  if (!playing) {
    return
  }
  pushToMaxLengthArray(renderState.aiLogs, line, 50)
  if(line.indexOf(" Action (swipe_")>-1)
    playSound("swipe")
  //renderAiLogs(renderState.aiLogs)
  //renderAiLogLine(line)

  if(line.indexOf(" Action ")>-1){
     actionHistoryEl.innerHTML = `<pre>${parseActionLog(line)}</pre>`;
   }
   else{
    lineBuffer.push(transformAiLogs(line));
    if(line.indexOf("Chose")>-1){
      lineBuffer.map( ln => aiLogEl.prepend(ln));
      lineBuffer = [] 
    }
    aiLogChildren++;
    if(aiLogChildren > 20){
      aiLogEl.removeChild(aiLogEl.lastChild);
    }
   }
}

function transformAiLogs(log){
  const el = document.createElement('div')
  var str = ""
  var split = log.split(" ")
  switch (split[0]){
    case "Chose":
      str =
        `<div class="ai-choice-label">${emoji("Chose")} ${emoji(split[1].toUpperCase())}</div></div>`
      break
    case "Sending":
      var lastCommand = split[2].split("|")
      str += emoji("Sending message:")+"<br>"
      str += replaceWithEmojis(lastCommand.slice(0,4).join(" ").replaceAll("-",""))+ (lastCommand[4] ? lastCommand[4] : "")
      str += "<br>"+replaceWithEmojis("clock1 clock2 clock3")
      break
    case "Step":
      str = emoji("Step")+" "+replaceWithEmojis(split[1])+ emoji("space") +
      emoji("right_arrow") +replaceWithEmojis(stripParens(split[2]))+ emoji("left_arrow") +"<br>" +
      emoji("Reward") + replaceWithEmojis(stripParens(split[5]))

      break
    case "received":
      str = replaceWithEmojis("received message:") + "<br>" + replaceWithEmojis(split[2].replaceAll("|","  "))
      break
    case "Safeguarded":
      str = replaceWithEmojis(split.slice(0,2).join(" "))
      break
    }
    el.innerHTML = str
  return el
}

/// Websocket Events

ws.onopen = function() {
  console.log('connection was established');
  setupUserInteraction();
  start_time = performance.now();
  requestImage();

  // set up interval such that if we haven't gotten an image in a while we request more
  setInterval(() => {
    if (performance.now() - request_start_time > 1000) {
      requestImage();
    }
  }, 300);
};

ws.onmessage = function(evt) {
  if (typeof evt.data === 'string') {
    try {
      const message = JSON.parse(evt.data)
      switch (message.type) {
        case 'curState':
          handleCurStateUpdate(message.data)
          break
        case 'aiAction':
          handleAIActionUpdate(message.data)
          break
        case 'aiLogLine':
          handleAILogLineUpdate(message.data)
          break
      }
    } catch (err) {
      console.log('JSON DECODE ERROR!', err);
    }
  } else {
    handleImageMessage(evt.data);
  }
};

/// User Interaction

function setupUserInteraction() {
  console.log('setting up user interaction...')
  window.addEventListener('keydown', e => {
    if (e.keyCode === 32) { // spacebar
      playing = !playing
    }
  })
}
