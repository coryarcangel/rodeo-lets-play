var gaugeNeedles = {}
function simData(){
	return {
		"gpu0":{
			"decUtil":null,
			"gpuUtil":null,
			"encUtil":null,
			"memUtil":null,
			"temp":30 + Math.floor(Math.random()*20),
			"pwrDraw":20+Math.floor(Math.random()*60)
		},
		"gpu1":{
			"decUtil":null,
			"gpuUtil":44,
			"encUtil":null,
			"memUtil":11,
			"temp":54 + Math.floor(Math.random()*20),
			"pwrDraw":20+Math.floor(Math.random()*60)
		}
	}
}

function initGpuMonitors(){
	var data = simData();
	console.log(data)
	for(gpu in data){
		var html = ""
		var container = document.getElementById("gpus");
		html+= `<div id="${gpu}" class="gpu-monitor">
      	<label>${gpu}</label>
      	<div class="power gauge"><div class="needle"></div></div>
      	<div class="temp gauge"><div class="needle"></div></div>
      </div>`;
		container.innerHTML += html;
	}
	//need all gaugeNeedles to render before we save them
	for(gpu in data){
		gaugeNeedles[gpu] = {
			'temp': document.querySelector("#"+gpu+" .temp .needle"),
			'power': document.querySelector("#"+gpu+" .power .needle")
		}
	}
}

function renderGpuMonitors(){
	var data = simData();
	for(gpu in data){
		gaugeNeedles[gpu]["power"]['style']['transform'] = 'rotate('+(data[gpu]["pwrDraw"]-25)+'deg)'
		gaugeNeedles[gpu]["temp"]['style']['transform'] = 'rotate('+(data[gpu]["temp"]-25)+'deg)'
	}
}

initGpuMonitors();

setInterval(function(){
	renderGpuMonitors();
},100)