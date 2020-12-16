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
  const [staticInfo, lscpu, dynamicSystemInfo, gpuStats] = await Promise.all([
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

    runCommand('nvidia-smi stats -d pwrDraw,temp,gpuUtil,memUtil,encUtil,decUtil,procClk,memClk -c 1').then(lines => {
      const gpuStats = {}
      lines.forEach(l => {
        const [device, key, _, value] = l.split(',').map(p => p.trim())
        if (!device) return

        const deviceKey = `gpu${device}`
        if (!gpuStats[deviceKey]) {
          gpuStats[deviceKey] = {}
        }

        const obj = gpuStats[deviceKey]
        if (!obj[key] || Number(value) > obj[key]) {
          obj[key] = Number(value) || null
        }
      })

      return gpuStats
    }),

    // runCommand('nvidia-smi -q --display=POWER,TEMPERATURE,MEMORY,PIDS'),

  ])

  return { ...staticInfo, lscpu, dynamicSystemInfo, gpuStats }
}

module.exports = { getSystemInfoObject }
