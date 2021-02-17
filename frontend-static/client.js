var img = document.getElementById('liveImg');
var fpsText = document.getElementById('fps');
var frameNumText = document.getElementById('frameNum');
var actionHistoryEl = document.getElementById('action-history');
var aiLogEl = document.getElementById('ai-log');
var stateActionsEl = document.getElementById('state-actions');
var objectAnnCanvas = document.getElementById('object-annotations');
var stats = document.getElementById('stats');
var titleEl = document.getElementById('rodeo');

var target_fps = 20;

var request_start_time = performance.now();
var start_time = performance.now();
var time = 0;
var request_time = 0;
var time_smoothing = 0.9; // larger=more smoothing
var request_time_smoothing = 0.2; // larger=more smoothing
var target_time = 1000 / target_fps;

var barGraph, ridgeGraph;
const radialOpt = {
  margin: {top: 0, right: 100, bottom: 0, left: 0},
    width: 320,
    height: 400
}
const ridgeOpt = {
   margin: {top: 50, right: 0, bottom: 0, left: 0},
    width: document.getElementById("gpus").offsetWidth,
    height: document.getElementById("gpus").offsetHeight
}

var gpuGraphData = {};

var barSize = 20;

var gaugeNeedles = {}

var sounds = {
  'tap_location': {src:'tap.mp3'},
  'double_tap_location':{src:'tap.mp3'} ,
  'reset': {src:'windows_startup.mp3', delay: 3500}
};

const Marquee = dynamicMarquee.Marquee;

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
      swipe_left: emoji("left_arrow")+ emoji("point")
    }

    titleEl.innerHTML = `${emoji("goat")} ⋆ ${emoji("rabbit")}  ${emoji("ribbon")}  /𝓇${emoji("blueheart")}ʊˈ𝒹𝑒ɪ❤ʊ/ 𝐿𝑒𝓉𝓈 𝒫𝓁𝒶𝓎 𝐻${emoji("hearteyes")}𝐿𝐿𝒴𝒲${emoji("cookie")}❤𝒟 𝓋 𝟣.♡  🎀  ${emoji("rabbit")} ⋆ ${emoji("goat")}`

});

function replaceWithEmojis(str){
    var re = new RegExp(Object.keys(emojiPositions).join("|"),"gi");
    return str.replace(re, function(matched){
      if(matched.indexOf("tap")>-1)
      console.log("matched",matched)
        return emoji(matched);
    });
}

function stripStrings(substrings,str){
    var re = new RegExp(substrings.join("|"),"gi");
    return str.replace(re,"");
}

var emojiSize = 16;


function emoji(emojiName) {
  var mapData = emojiPositions[emojiName] || [[0,0]];
  //make sure we have an array of arrays, in case multiple emojis should be shown
  var emojis = (typeof mapData[0] === "object" ? mapData : [mapData]);
  
  return emojis.map( emoj => `<span class='emoji' style="background-position: ${(emoj[0]*(emojiSize))} ${emoj[1]*emojiSize};"></span>`).join("");
}

function updateCurStateRender() {
  const { frameNum, fps, imageState, recentTouch, stateActions = [], systemInfo } = renderState;
  fpsText.textContent = fps+" fps";
  frameNumText.textContent = frameNum;

  renderImageState(imageState, recentTouch);
  //renderStateActions(stateActions);
  // renderBarGraph(stateActions);
  renderSystemInfo(systemInfo);
}

/// Image State Rendering

const labelColorsMap = {
  'person': colors['blueviolet'],
  'clock': colors['springgreen'],
  'tvmonitor': colors['black'],
  'laptop': colors['black'],
  'traffic light': colors['chartreuse'],
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
    sounds[sound].clip.play();
  }, sounds[sound].delay || 0)
}

initSound();

//to play a sound
//playSound("tap");


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
  // const w = window.innerWidth
  // const h = window.innerHeight
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
      fontSize: 14,
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
    ctx.lineWidth = 5;
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
    ctx.lineWidth = 5
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

function renderBarGraph(stateActions) {
    const actionEls = (stateActions || [])
    .filter(a => a.length > 1 && !!a[1].object_type) // only render tap object actions :)
    .map( (d,i) =>  {
      return {
        label: i+": "+d[1].img_obj.label,
        labelClean: d[1].img_obj.label,
        confidence: d[1].img_obj.confidence
      }
    }).filter(a => !!a.confidence);
    // console.log("graoh data",JSON.stringify(actionEls))
    drawBarGraph(actionEls);
}

function initBarGraph(){
  if(barGraph){
    barGraph.remove()
    d3.selectAll("#bar_graph > svg").remove();
  }

  barGraph = d3.select("#bar_graph")
  .append("svg")
    .attr("width", radialOpt.width + radialOpt.margin.left + radialOpt.margin.right)
    .attr("height", radialOpt.height + radialOpt.margin.top + radialOpt.margin.bottom)
  .append("g")
    .attr("transform",
          "translate(" + radialOpt.margin.left + "," + radialOpt.margin.top + ")");
}

function initRidgelineGraph(){
  if(ridgeGraph){
    ridgeGraph.remove()
    d3.selectAll("#gpus > svg").remove();
  }

  ridgeGraph = d3.select("#gpus")
  .append("svg")
    .attr("width", ridgeOpt.width + ridgeOpt.margin.left + ridgeOpt.margin.right)
    .attr("height", ridgeOpt.height + ridgeOpt.margin.top + ridgeOpt.margin.bottom)
  .append("g")
    .attr("transform",
          "translate(" + ridgeOpt.margin.left + "," + ridgeOpt.margin.top + ")");
}

function drawRidgelineGraph(data){
  initRidgelineGraph()
  var categories = Object.keys(data)
  var n = categories.length

  var x = d3.scaleLinear()
    .domain([0, 130])
    .range([ 0, ridgeOpt.width ]);
  ridgeGraph.append("g")
    .attr("transform", "translate(0," + ridgeOpt.height + ")")
    .call(d3.axisBottom(x));

  var y = d3.scaleLinear()
    .domain([0, 0.4])
    .range([ ridgeOpt.height, 0]);

  var yName = d3.scaleBand()
    .domain(categories)
    .range([0, ridgeOpt.height])
    .paddingInner(1)
  ridgeGraph.append("g")
    .call(d3.axisLeft(yName));

  // Compute kernel density estimation for each column:
  var kde = kernelDensityEstimator(kernelEpanechnikov(7), x.ticks(40)) // increase this 40 for more accurate density.
  var allDensity = []
  for (column in data) {
      key = column
      density = kde( data[column] )
      allDensity.push({key: key, density: density})
  }

  ridgeGraph.selectAll("areas")
    .data(allDensity)
    .enter()
    .append("path")
      .attr("transform", function(d){return("translate(0," + (yName(d.key)-ridgeOpt.height) +")" )})
      .datum(function(d){return(d.density)})
      .attr("fill", "#69b3a2")
      .attr("stroke", "#000")
      .attr("stroke-width", 1)
      .attr("d",  d3.line()
          .curve(d3.curveBasis)
          .x(function(d) { return x(d[0]); })
          .y(function(d) { return y(d[1]); })
      )  

  function kernelDensityEstimator(kernel, X) {
    return function(V) {
      return X.map(function(x) {
        return [x, d3.mean(V, function(v) { return kernel(x - v); })];
      });
    };
  }
  function kernelEpanechnikov(k) {
    return function(v) {
      return Math.abs(v /= k) <= 1 ? 0.75 * (1 - v * v) / k : 0;
    };
  }
}

function drawBarGraph(data){
  initBarGraph()

  var x = d3.scaleLinear()
    .domain([0, 1])
    .range([ 0,350]);

  var y = d3.scaleBand()
    .range([ 0, (data.length)*(2+barSize) ])
    .domain(data.map(function(d) { return d.label; }))

  barGraph.append("g")
    // .call(d3.axisLeft(y))
    .data(data)
    .call(d3.axisLeft(y))
    .selectAll("text")
    .attr("y", function(d,i) { y(d) })
    .attr("x", function(d,i) { return x(data[i]['confidence']); }) 
    .attr("transform", function(d){ return "translate("+ 15 +",0)" })
    .attr("text-anchor","start")
    .attr("font-family",'Helvetica Neue Roman')
    .attr("font-size","18px")
    .attr("fill","black")

  // Bars
  barGraph.selectAll("mybar")
    .data(data)
    .enter()
    .append("rect")
      .attr("x", 10)
      .attr("y", function(d,i) { return i*(2+barSize); })
      .attr("width", function(d) { return x(d['confidence']); })
      .attr("height", barSize)
      .attr("stroke", function(d,i){ return labelColorsMap[d['labelClean']] ? labelColorsMap[d['labelClean']] : "black" })
      .attr("fill", function(d,i){ return labelColorsMap[d['labelClean']] ? labelColorsMap[d['labelClean']] : "black" });//")
}

function initGpuMonitors(gpuData){

  for(gpu in gpuData){
    gpuGraphData[gpu+" power"] = []
    gpuGraphData[gpu+" temp"] = []
  }
}

var wattRange = [15,85]// [min, diffBtwMinMax]
var tempRange = [20,160]
function renderGpuMonitors(gpuData){

  for(gpu in gpuData){
    gpuGraphData[gpu+" power"].push(gpuData[gpu]["pwrDraw"] + (Math.floor(Math.random()*8)-4));
    //FIFO 250 elements long
    if(gpuGraphData[gpu+" temp"].push(gpuData[gpu]["temp"] + (Math.floor(Math.random()*8)-4)) > 250){
      gpuGraphData[gpu+" power"].shift();
      gpuGraphData[gpu+" temp"].shift();
    }
  }
  drawRidgelineGraph(gpuGraphData);
}

function renderActionHistory(actionHistory) {
  // reverse order because of the way we store the history ;p
  const actionEls = []
  for (let i = (actionHistory || []).length - 1; i >= 0; i--) {
    const a = actionHistory[i]
    const { type, label, p, prob } = a
    const el = document.createElement('div')
    const text = [
      `History #${i + 1}:`,
      type,
      label !== type ? label : '',
      p ? `(${p[0]}, ${p[1]})` : '',
      prob !== undefined ? `- ${((prob || 0) * 100).toFixed(1)}% chance` : '',
    ].join(' ')
    el.textContent = text
    actionEls.push(el)
  }

  actionHistoryEl.innerHTML = ``
  actionHistoryEl.append(...actionEls)
}


function parseActionLog(actionString){
  //actionString = `Step 85 (1803) - Action (double_tap_location, {"x": 824, "y": 466, "type": "object", "object_type": "Circle #7", "img_obj": {"rect": [785, 427, 78, 78], "label": "Circle #7", "confidence": null, "object_type": "circle"}})`
  var split = actionString.split(" ");
  var actionNumber = split[1];
  var actionType = split[5].slice(1,-1).replace("(","")
  console.log("oh yah",actionType)
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

function transformAiLogs(log){ 
  const el = document.createElement('div')
  var str = ""
  var split = log.split(" ")
  //${replaceWithEmojis('DEEP_Q Heuristic RANDOM point')}
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
      str = log
      break
    }
    el.innerHTML = str
  return el
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
    // const el = document.createElement('div')
    // el.innerHTML = replaceWithEmojis(noActions[i])
    // logEls.push(el)
    logEls.push(transformAiLogs(noActions[i]))
  }

  aiLogEl.innerHTML = ``
  aiLogEl.append(...logEls)
}

function renderSystemInfo(systemInfo) {
  // console.log('system info', systemInfo)
  if (!systemInfo) {
    return
  }
  const gpuData = systemInfo.gpuStats;
  //update gpu stat fifos
  if(!gpuGraphData['gpu0 power']){
        initGpuMonitors(gpuData)
        initRidgelineGraph();
    }
    renderGpuMonitors(gpuData)
  // stats.innerHTML = JSON.stringify(systemInfo)

  // TODO: henry here will be a json object with various keys you can log and play with.
  // some docs: https://github.com/sebhildebrandt/systeminformation
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

  renderState.frameNum = data.frameNum;
  renderState.imageState = parseMessageKey(data, 'imageState')
  renderState.systemInfo = parseMessageKey(data, 'systemInfo')

  const aiStatus = parseMessageKey(data, 'aiStatus') || {}
  renderState.stateActions = aiStatus.actions || []
  renderState.aiReward = aiStatus.reward || 0
  renderState.aiStepNum = aiStatus.step_num || 0
  renderState.aiPolicyChoice = aiStatus.policy_choice
  renderState.aiRecentActionStepNums = aiStatus.recent_action_step_nums

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
  if(sounds && sounds[data.type])
    playSound(data.type)

  if (data.type === 'tap_location' || data.type === 'double_tap_location') {
    renderState.recentTouch = data
  } else {
    renderState.recentTouch = null
  }

  pushToMaxLengthArray(renderState.actionHistory, data, 100)
  //renderActionHistory(renderState.actionHistory)
}

function handleAILogLineUpdate(line) {
  if (!playing) {
    return
  }
  pushToMaxLengthArray(renderState.aiLogs, line, 100)
  renderAiLogs(renderState.aiLogs)
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
