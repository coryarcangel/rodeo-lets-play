const util = require('util')
const childProcess = require('child_process')
const si = require('systeminformation')

const exec = util.promisify(childProcess.exec)

async function runCommand(cmd) {
  try {
    const { stdout } = await exec(cmd)
    return stdout.split('\n').map(line => line.trim())
  } catch (e) {
    console.error(e) // should contain code (exit code) and signal (that caused the termination).
    return ['']
  }
}

// will get info like cpu usage, gpu, etc for publishing to redis

let _staticInfo = null
async function getStaticSystemInfo() {
  if (_staticInfo) {
    return _staticInfo
  }

  const [uname, staticSystemInfo] = await Promise.all([
    runCommand('uname -a').then(lines => lines[0]),
    si.getStaticData(),
  ])

  _staticInfo = { uname, staticSystemInfo }
  return _staticInfo
}

async function getSystemInfoObject() {
  const [staticInfo, lscpu, dynamicSystemInfo] = await Promise.all([
    getStaticSystemInfo(),

    runCommand('lscpu').then(lines => {
      const data = {}
      lines.forEach(l => {
        const [key, value] = l.split(':').map(p => p.trim())
        data[key] = value || ''
      })
      return data
    }),

    si.get({
      currentLoad: '*',
      fullLoad: '*',
      cpuCurrentspeed: '*',
      cpuTemperature: '*',
      mem: '*',
      battery: '*',
      processes: 'running, list',
      disksIO: '*',
      fsStats: 'rx_sec, wx_sec, tx_sec',
      networkStats: '*',
    }),

    // runCommand('nvidia-smi stats'),
    //
    // runCommand('nvidia-smi -q --display=POWER,TEMPERATURE,MEMORY,PIDS'),

  ])

  return { ...staticInfo, lscpu, dynamicSystemInfo }
}

module.exports = { getSystemInfoObject }

getSystemInfoObject().then(d => {
  console.log(d)
})
